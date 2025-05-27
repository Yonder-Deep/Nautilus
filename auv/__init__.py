from __future__ import annotations # Depending on your version of python
import multiprocessing
from multiprocessing.shared_memory import SharedMemory
import threading
import platform
from queue import Queue, Empty
from typing import List
from time import time
from pathlib import Path

#from api import IMU
#from api import PressureSensor
#from api import Indicator
from api.gps import GPS
from api.abstract import AbstractController
if platform.system() == "Linux":
    from api.motor_controller import MotorController
else:
    from api.mock_controller import MockController as MotorController

from core.main import main_log, motor_test
from core.websocket_handler import websocket_server as websocket_thread
from core.control import Control
from core.localization import Localization
from core.navigation import Navigation

from models.data_types import *
from models.shared_memory import create_shared_state
from models.execution import Executor

from pydantic import BaseModel
from pydantic_yaml import parse_yaml_file_as
from ruamel.yaml import YAML
yaml = YAML(typ='safe')

class ConfigSchema(BaseModel):
    simulation: bool 
    socket_ip: str
    socket_port: int
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
    print("STARTUP WITH CONFIGURATION:")
    print(config.model_dump())

    # Anything put into this queue will be printed
    # to stdout & forwarded to frontend
    logging_queue = Queue()

    # For tracking and cleanup
    executors: List[Executor] = []
    shared_memories: List[SharedMemory] = []

    # Websocket Initialization
    queue_to_base = Queue()
    queue_from_base= Queue()
    ws_shutdown_q = Queue() # This just takes the single shutdown method for the websocket server
    ws_stop = threading.Event()
    ws_inner = threading.Thread(
            target=websocket_thread,
            kwargs={'stop_event': ws_stop,
                    'logging_q':logging_queue,
                    'websocket_interface': config.socket_ip,
                    'websocket_port': config.socket_port,
                    'ping_interval': config.ping_interval,
                    'queue_to_base': queue_to_base,
                    'queue_from_base': queue_from_base,
                    'verbose': True,
                    'shutdown_q': ws_shutdown_q})
    ws_exec = Executor(
        type="Thread",
        value=ws_inner,
        input_q=queue_to_base,
        stop_event=ws_stop,
    )
    executors.append(ws_exec)
    ws_exec.start()
    ws_shutdown = ws_shutdown_q.get(block=True) # Needed to shut down server

    # DI the motor controller
    motor_controller: AbstractController = MotorController()

    # Control System Initialization
    shared_state_name = "shared_state"
    measured_state = create_shared_state(name=shared_state_name);
    shared_memories.append(measured_state)

    queue_input_nav = Queue() # Input from user & state input to nav
    control_desired_q = Queue() # Setpoint input to nav
    nav_stop = threading.Event()
    navigation_inner = Navigation(
            input_state_q=queue_input_nav,
            desired_state_q=control_desired_q,
            logging_q=logging_queue,
            stop_event=nav_stop
    )
    navigation_exec = Executor(
            type="Thread",
            value=navigation_inner,
            input_q=queue_input_nav,
            stop_event=nav_stop,
    )
    executors.append(navigation_exec)
    disable_control_event = threading.Event()
    control_stop = threading.Event()
    control_inner = Control(
            input_shared_state=shared_state_name,
            desired_state_q=control_desired_q,
            logging_q=logging_queue,
            controller=motor_controller,
            stop_event=control_stop,
            disabled_event=disable_control_event,
    )
    control_exec = Executor(
            type="Thread",
            value=control_inner,
            input_q=control_desired_q,
            stop_event=control_stop,
    )
    executors.append(control_exec)
    
    if platform.system == "Linux":
        from api.localization import localize, localize_setup
        localization_input_q = multiprocessing.Queue()
        localization_stop = multiprocessing.Event()
        localization_inner = Localization(
                stop_event=localization_stop,
                input_q=localization_input_q,
                output_shared_memory=shared_state_name,
                setup_args=localize_setup(),
                localize_func=localize,
        )
        localization_exec = Executor(
                type="Process",
                value=localization_inner,
                input_q=localization_input_q,
                stop_event=localization_stop,
        )
    else:
        from core.localization import Mock_Localization
        localization_input_q = Queue()
        localization_stop = threading.Event()
        localization_inner = Mock_Localization(
                stop_event=localization_stop,
                output=shared_state_name,
                localize_func=motor_controller.get_state
        )
        localization_exec = Executor(
                type="Process",
                value=localization_inner,
                input_q=localization_input_q,
                stop_event=localization_stop,
        )
    executors.append(localization_exec)
    localization_exec.start()

    print("Beginning main loop")
    try:
        promises: List[Promise] = []
        while True:
            main_log(logging_queue, queue_to_base)

            try:
                current_time = time()
                for promise in promises:
                    if current_time - promise.init > promise.duration:
                        promises.remove(promise)
                        promise.callback()
                    
                message_from_base = queue_from_base.get_nowait()
                # Based on commands, execute functions and/or subroutines
                if message_from_base:
                    print("Message from base: " + str(message_from_base))
                    command = message_from_base["command"]
                    if command == "pid":
                        print("Changing PID constants not yet implemented")

                    elif command == "motor":
                        print("Starting motor test")
                        motor_test(
                            motor_controller,
                            message_from_base["content"],
                            promises=promises,
                            disable_controller=disable_control_event,
                        )

                    elif command == "ctl":
                        print("Starting heading test")
                        control_desired_q.put(message_from_base["content"])

                    elif command == "nav":
                        print("Beginning mission")
                        goal_coordinate = message_from_base["content"]
                        print("Goal: " + str(goal_coordinate))
                        if not navigation_exec.value.is_alive():
                            navigation_exec.value.start()
                            control_exec.value.start()
                        queue_input_nav.put(goal_coordinate)

            except Empty:
                pass

    except KeyboardInterrupt:
        print("Joining threads")
        ws_shutdown() # The WS server blocks, so has custom shutdown
        for executor in executors:
            if executor.value.is_alive():
                executor.stop()
                executor.value.join()
        print("Closing shared memory")
        for shm in shared_memories:
            shm.close()
            shm.unlink()
        print("All threads and processes joined, all shared memory released, process exiting")
