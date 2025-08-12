""" The main functions for the main __init__ thread, to react to commands from
    base and oversee general instructions for the other threads.
"""

from typing import Dict, Tuple, List, Union, Optional, Any, Callable
from queue import Queue, Empty, Full
from time import time

import msgspec

from api.abstract import AbstractController
from models.data_types import Promise, MotorSpeeds, Log, State, SerialState
from models.tasks import Task

# This is the shorthand log function used in the main thread
def log(x: Any):
    print("\033[42mMAIN:\033[0m " + str(x))

# Down here are the actual log parsing functions for actual Log objects
log_prefixes: Dict[str, str] = {
    "MAIN": "\033[42mMAIN:\033[0m ",
    "CTRL": "\033[43mCONTROL:\033[0m ",
    "NAV": "\033[44mNAV:\033[0m ",
    "WSKT": "\033[45mWEBSOCKET:\033[0m ",
    "LCAL": "\033[46mLOCALIZE:\033[0m ",
    "PRCP": "\033[46mPERCEPT:\033[0m ",
}

def handle_log(message: Union[Log, str], base_q: Queue):
    try:
        if isinstance(message, str):
            raise Exception
        print_log: bool = True
        if message.type == "state" and isinstance(message.content, SerialState): 
            print_log = False
            message.content = message.content.model_dump_json()
        # Since message: Log, we must convert Log to JSON
        result = msgspec.json.encode(message).decode()
        if message.dest == "BASE":
            try:
                base_q.put_nowait(result)
            except Full:
                pass
        if print_log:
            if message.dest == "BASE":
                print("\033[101mTO BASE: " + str(message) + "\033[0m")
            print(log_prefixes[message.source] + str(message.content))
    except:
            print("\033[41mError handling log:\033[0m " + str(message))

def motor_test(
    speeds:Tuple[float, float, float, float],
    *,
    motor_controller:AbstractController,
    promises: List[Promise],
    disable_controller: Callable,
    time_to_zero: float = 10.0
) -> None:
    """ Safely parse the speeds and dispatch them to the motor controller. Also
        handles disabling any PID control execution while the motor test is
        underway. Also adds a promise to zero the motors after a default of 10
        seconds, which can be customized via `time_to_zero`.
    """
    try:
        disable_controller()
        motor_speeds = MotorSpeeds(
            forward = speeds[0],
            turn = speeds[1],
            front = speeds[2],
            back = speeds[3],
        )
        motor_controller.set_speeds(motor_speeds, verbose=True)
        log("Set motor speeds: " + motor_speeds.model_dump_json())
    except ValueError as e:
        log("Motor speeds invalid: " + str(speeds))
        log(e)
    finally:
        noExistingPromise = True 
        for promise in promises:
            if promise.name=="motorReset":
                promise.init = time()
                noExistingPromise = False 
                log("Mutated existing motor reset promise")
        if noExistingPromise: 
            promises.append(Promise(
                name="motorReset",
                duration = time_to_zero,
                callback = lambda: motor_controller.set_zeros()
            ))
            log("Appended motor reset promise")

def manage_tasks(msg, tasks: List[Task], logging_q: Queue):
    subcommand: str = msg["content"]["sub"]
    try:
        if subcommand == "info":
            pass
        elif subcommand == "enable":
            matching_task = [task for task in tasks if task.meta.name == msg["content"]["task"]][0]
            log("Activating task: " + matching_task.meta.name)
            matching_task.activate()
        elif subcommand == "disable":
            matching_task = [task for task in tasks if task.meta.name == msg["content"]["task"]][0]
            log("Deactivating task: " + matching_task.meta.name)
            matching_task.deactivate()
    except Exception as e:
        log("Error parsing/executing subcommand in manage_tasks: ")
        log(e)

    state_map = {
        True: "active",
        False: "inactive",
    }
    task_state: dict[str, str] = {}
    for task in tasks:
        task_state[task.meta.name] = state_map[task.meta.active]
    response = Log(
        source="MAIN",
        type="tasks",
        content=task_state,
        dest="BASE",
    )
    log("Task info: " + msgspec.json.encode(response).decode())
    logging_q.put(response)
