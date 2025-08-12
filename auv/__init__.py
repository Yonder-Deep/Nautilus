from models.data_types import *
from models.shared_memory import create_shared_state
from models.tasks import Task

from core.main import handle_log, motor_test, log, manage_tasks
from core.websocket_handler import WebsocketHandler
from core.control import Control
from core.localization import Localization
from core.navigation import Navigation

from api.gps import GPS
from api.abstract import AbstractController

import multiprocessing
from multiprocessing.shared_memory import SharedMemory
import threading
from queue import Queue, Empty
from typing import List, Literal
from time import time
from pathlib import Path

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
    logging_pqueue = multiprocessing.Queue()

    # For tracking and cleanup
    tasks: List[Task] = []
    shared_memories: List[SharedMemory] = []

    # Websocket Initialization
    queue_to_base = Queue(maxsize=10) # When there's no connection, messages pile up
    queue_from_base= Queue()
    ws_shutdown_q = Queue() # This just takes the single shutdown method for the websocket server
    ws_task = WebsocketHandler(
        websocket_interface=config.socket_ip,
        websocket_port=config.socket_port,
        ping_interval=config.ping_interval,
        queue_to_base=queue_to_base,
        queue_from_base=queue_from_base,
        verbose=True,
        shutdown_q=ws_shutdown_q,
        logging_q=logging_queue,
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
    navigation_task: Task = Navigation(
        logging_q=logging_queue,
        desired_state_q=control_desired_q,
    )
    tasks.append(navigation_task)

    control_task: Task = Control(
        shared_state_name=shared_state_name,
        logging_q=logging_queue,
        controller=motor_controller,
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
        localization_task: Task = Localization(
            logging_q=logging_pqueue,
            output_shared_memory=shared_state_name,
            setup_args=localize_setup(),
            kalman_filter=localize,
            depth_func=depth_func,
        )
    else:
        from core.localization import Mock_Localization
        localization_task = Mock_Localization(
            output=shared_state_name,
            logging_q=logging_queue,
            localize_func=motor_controller.get_state,
        )
    tasks.append(localization_task)

    if config.perception:
        from core.perception import Perception
        perception_task = Perception(
            logging_q=logging_pqueue,
            camera_path=config.camera_path,
            ip=config.video_ip,
            port=config.video_port,
            fps=30,
        )
        tasks.append(perception_task)

    promises: List[Promise] = []
    dispatch: dict[
        Literal["pid", "motor", "control", "mission", "tasks", "promise"],
        Dispatch,
    ] = {
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
                disable_controller=control_task.deactivate,
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
        "promise": Dispatch(
            log="Registering promise",
            func=lambda msg: promises.append(msg),
        ),
    }

    try:
        control_task.startup()
        localization_task.startup()
        initial_task_log: str = "Tasks: "
        for task in tasks:
            initial_task_log += "\n\t" + str(task) + "\n\t" + str(task.meta) + "\n"
        log(initial_task_log)
        del initial_task_log
        log("Beginning main loop")
        while True:
            # Parse logs
            while True:
                try:
                    log_msg: Union[Log, str] = logging_queue.get_nowait()
                    if log_msg:
                        handle_log(log_msg, queue_to_base)
                except Empty:
                    break

            # Check promises
            for promise in promises:
                if time() - promise.init > promise.duration:
                    promises.remove(promise)
                    promise.callback()

            # Based on commands, dispatch functions and/or subroutines
            try:
                message = queue_from_base.get_nowait()
                if message:
                    log("Evaluating dispatch: " + str(message))
                    if dispatch[message["command"]]:
                        log("DISPATCH: " + dispatch[message["command"]].log)
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
            if task.meta.started:
                task.shutdown()
                task.join()
        log("Closing shared memory")
        for shm in shared_memories:
            shm.close()
            shm.unlink()
        log("All tasks joined, all shared memory released, process exiting")
