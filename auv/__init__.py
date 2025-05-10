from __future__ import annotations # Depending on your version of python
import threading
import platform
from queue import Queue, Empty
from multiprocessing import Queue as MP_Queue
from typing import Tuple, List
import time
import asyncio
from pathlib import Path

#from api import IMU
#from api import PressureSensor
#from api import Indicator
from api.gps import GPS
from api.abstract import AbstractController
from api.motor_controller import MotorController
from api.mock_controller import MockController

import config
from core import \
    websocket_thread,\
    Navigation, \
    Control, \
    motor_speeds, \
    main_log
from custom_types import *

from pydantic import BaseModel
from pydantic_yaml import parse_yaml_file_as
from ruamel.yaml import YAML
yaml = YAML(typ='safe')

class ConfigSchema(BaseModel):
    testing_mode: bool 
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

config = load_config()
print("STARTUP WITH CONFIGURATION:")
print(config.model_dump())

if __name__ == "__main__":
    # This event is set so that all the threads know to end
    stop_event = threading.Event()

    # Anything put into this queue will be printed
    # to stdout & forwarded to frontend
    logging_queue = Queue()

    # Used for thread cleanup
    threads = []

    # Websocket Initialization
    queue_to_base = Queue()
    queue_to_auv = Queue()
    ws_shutdown_q = Queue() # This just takes the single shutdown method for the websocket server
    ws_thread = threading.Thread(
            target=websocket_thread,
            kwargs={'stop_event':stop_event,
                    'logging_event':logging_queue,
                    'websocket_interface': config.socket_ip,
                    'websocket_port': config.socket_port,
                    'ping_interval': config.ping_interval,
                    'queue_to_base': queue_to_base,
                    'queue_to_auv': queue_to_auv,
                    'verbose': True,
                    'shutdown_q': ws_shutdown_q})
    threads.append(ws_thread)
    ws_thread.start()
    ws_shutdown = ws_shutdown_q.get(block=True) # Needed to shut down server

    motor_controller: AbstractController = MotorController()
    if platform.system() == "Darwin":
        motor_controller = MockController()

    # Control System Initialization
    queue_input_nav = Queue() # Input from user & state input to nav
    control_state_q = Queue() # State input to nav
    control_desired_q = Queue() # Setpoint input to nav
    navigation_thread = Navigation(
            input_state_q=queue_input_nav,
            desired_state_q=control_desired_q,
            logging_q=logging_queue,
            stop_event=stop_event
    )
    control_thread = Control(
            input_state_q=control_state_q,
            desired_state_q=control_desired_q,
            logging_q=logging_queue,
            controller=motor_controller,
            stop_event=stop_event
    )

    if platform.system() == "Linux":
        """gps_queue=Queue()
        gps_thread = GPS(
            out_queue=gps_queue,
            path=config.gps_path,
            stop_event=stop_event
        )"""
        from core.localization import Localization
        localization_q = MP_Queue()
        localization_thread = Localization(
            stop_event=stop_event,
            output_q=localization_q
        )

    print("Beginning main loop")
    try:
        promises: List[Promise] = []
        while True:
            main_log(logging_queue, queue_to_base)

            try:
                current_time = time.time()
                for promise in promises:
                    if current_time - promise.init > promise.duration:
                        promises.remove(promise)
                        promise.callback()
                    
                message_from_base = queue_to_auv.get_nowait()
                # Based on commands, execute functions and/or subroutines
                if message_from_base:
                    print("Message from base: " + str(message_from_base))
                    command = message_from_base["command"]
                    if command == "pidConstants":
                        print("Setting PID Constants")

                    elif command == "motorTest":
                        print("Starting motor test")
                        motor_speeds(
                            motor_controller,
                            message_from_base["content"],
                            promises=promises
                        )

                    elif command == "headingTest":
                        print("Starting heading test")
                        control_desired_q.put(message_from_base["content"])

                    elif command == "mission":
                        print("Beginning mission")
                        goal_coordinate = message_from_base["content"]
                        print("Goal: " + str(goal_coordinate))
                        if not navigation_thread.is_alive():
                            threads.append(navigation_thread)
                            navigation_thread.start()
                            threads.append(control_thread)
                            control_thread.start()
                        queue_input_nav.put(goal_coordinate)

            except Empty:
                pass

    except KeyboardInterrupt:
        stop_event.set()
        print("Joining threads")
        ws_shutdown()
        for thread in threads:
            if thread.is_alive():
                thread.join()
        print("All threads joined, process exiting")
