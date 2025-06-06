from models.data_types import *
from models.shared_memory import create_shared_state
from models.tasks import Task, task_factory

from core.main import main_log, motor_test, log, manage_tasks
from core.websocket_handler import websocket_server as websocket_thread
from core.control import Control
from core.localization import Localization
from core.navigation import Navigation

from api.gps import GPS
from api.abstract import AbstractController

import multiprocessing
from multiprocessing.shared_memory import SharedMemory
import threading
from queue import Queue, Empty
from typing import List
from time import time
from pathlib import Path
import json

from pydantic import BaseModel
from pydantic_yaml import parse_yaml_file_as
from ruamel.yaml import YAML
yaml = YAML(typ='safe')

class ConfigSchema(BaseModel):
    simulation: bool 
    socket_ip: str
    socket_port: int
    perception: bool
    video_ip: str
    video_port: int
    camera_path: str
    ping_interval: int
    gps_path: str

def load_config() -> ConfigSchema:
    default_config = parse_yaml_file_as(ConfigSchema, 'data/config.yaml').model_dump()
    local_path = Path('data/local/config.yaml')
    if local_path.exists():
        local_file = open(local_path, 'r')
        local_config = yaml.load(local_file)
        local_file.close()
        local_filtered = {k:v for (k,v) in local_config.items() if v}
        default_config.update(local_filtered)
    return ConfigSchema(**default_config)

if __name__ == "__main__":
    config = load_config()
    log("STARTUP WITH CONFIGURATION:\n" + config.model_dump_json(indent=2))

    # Anything put into this queue will be printed
    # to stdout & forwarded to frontend
    logging_queue = Queue()

    # For tracking and cleanup
    tasks: List[Task] = []
    shared_memories: List[SharedMemory] = []

    # Websocket Initialization
    queue_to_base = Queue(maxsize=10) # When there's no connection, messages pile up
    queue_from_base= Queue()
    ws_shutdown_q = Queue() # This just takes the single shutdown method for the websocket server
    ws_stop = threading.Event()
    ws_inner = threading.Thread(
            target=websocket_thread,
            name="Websocket",
            kwargs={'stop_event': ws_stop,
                    'logging_q':logging_queue,
                    'websocket_interface': config.socket_ip,
                    'websocket_port': config.socket_port,
                    'ping_interval': config.ping_interval,
                    'queue_to_base': queue_to_base,
                    'queue_from_base': queue_from_base,
                    'verbose': True,
                    'shutdown_q': ws_shutdown_q}
    )
    ws_task = Task(
        name="Websocket",
        type="Thread",
        value=ws_inner,
        input_q=queue_to_base,
        stop_event=ws_stop,
    )
    tasks.append(ws_task)
    ws_task.start()
    ws_shutdown = ws_shutdown_q.get(block=True) # Needed for stopping server

    # DI the motor controller
    if not config.simulation:
        from api.motor_controller import MotorController
    else:
        from api.mock_controller import MockController as MotorController
    motor_controller: AbstractController = MotorController(log)

    # Control System Initialization
    shared_state_name = "shared_state"
    measured_state = create_shared_state(name=shared_state_name)
    shared_memories.append(measured_state)

    control_desired_q = Queue() # Setpoint input to nav
    navigation_task = task_factory(
            constructor=Navigation,
            name="Navigation",
            input_q=queue.Queue(),
            stop_event=threading.Event(),
            logging_q=logging_queue,
            desired_state_q=control_desired_q,
    )
    tasks.append(navigation_task)

    disable_control_event = threading.Event()
    control_task = task_factory(
            constructor=Control,
            name="Control",
            input_q=control_desired_q,
            stop_event=threading.Event(),
            input_shared_state=shared_state_name,
            logging_q=logging_queue,
            controller=motor_controller,
            disabled_event=disable_control_event,
    )
    tasks.append(control_task)
    
    # Initialize the real or fake localization task
    if not config.simulation:
        from api.localization import localize, localize_setup
        def depth_func() -> float:
            return 0.
        # TODO: Convert this to task factory
        localization_input_q = multiprocessing.Queue()
        localization_stop = multiprocessing.Event()
        localization_inner = Localization(
                stop_event=localization_stop,
                input_q=localization_input_q,
                output_shared_memory=shared_state_name,
                setup_args=localize_setup(),
                kalman_filter=localize,
                depth_func=depth_func,
        )
        localization_task = Task(
                name="Localization",
                type="Process",
                value=localization_inner,
                input_q=localization_input_q,
                stop_event=localization_stop,
        )
    else:
        from core.localization import Mock_Localization
        localization_task = task_factory(
                Mock_Localization,
                name="Localization",
                input_q=Queue(),
                stop_event=threading.Event(),
                output=shared_state_name,
                logging_q=logging_queue,
                localize_func=motor_controller.get_state,
        )
    tasks.append(localization_task)

    if config.perception:
        from core.perception import Perception
        perception_task = task_factory(
                Perception,
                name="Perception",
                input_q=Queue(),
                stop_event=threading.Event(),
                camera_path=config.camera_path,
                ip=config.video_ip,
                port=config.video_port,
                fps=30,
        )

    promises: List[Promise] = []
    dispatch = {
        "pid": Dispatch(
                log="Changing PID constants",
                func=lambda msg: control_desired_q.put(msg),
        ),
        "motor": Dispatch(
                log="Starting motor test",
                func=lambda msg: motor_test(
                        msg["content"],
                        motor_controller=motor_controller,
                        promises=promises,
                        disable_controller=disable_control_event,
                ),
        ),
        "control": Dispatch(
                log="Starting PID test",
                func=lambda msg: control_task.input(msg),
        ),
        "mission": Dispatch(
                log="Beginning mission (loading trajectory)",
                func=lambda msg: navigation_task.input(msg["content"]),
        ),
        "tasks": Dispatch(
                log="Managing tasks",
                func=lambda msg: manage_tasks(msg, tasks=tasks, logging_q=logging_queue),
        ),
    }
    control_task.start()
    log("Tasks: ")
    for task in tasks:
        log(str(task))
    try:
        log("Beginning main loop")
        while True:
            # Parse logs
            main_log(logging_queue, queue_to_base)

            # Check promises
            for promise in promises:
                if time() - promise.init > promise.duration:
                    promises.remove(promise)
                    promise.callback()

            # Based on commands, dispatch functions and/or subroutines
            try:
                message = queue_from_base.get_nowait()
                if message:
                    log("Message from base: " + str(message))
                    if dispatch[message["command"]]:
                        log(dispatch[message["command"]].log)
                        dispatch[message["command"]].func(message)
                    else:
                        log("Dispatch function not found for: " \
                            + str(message["command"]))
            except Empty:
                pass

    except KeyboardInterrupt:
        log("Joining threads")
        ws_shutdown() # The WS server blocks, so has custom shutdown
        for task in tasks:
            if task.value.is_alive():
                task.stop()
                task.value.join()
        log("Closing shared memory")
        for shm in shared_memories:
            shm.close()
            shm.unlink()
        log("All tasks joined, all shared memory released, process exiting")
