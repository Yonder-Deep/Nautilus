""" The main functions for the main __init__ thread, to react to commands from
    base and oversee general instructions for the other threads.
"""

from typing import Dict, Tuple, List, Union, Optional, Any
from queue import Queue, Empty, Full
import threading
from time import time

import msgspec

from api.abstract import AbstractController
from models.data_types import Promise, MotorSpeeds, Log, State, SerialState
from models.tasks import Task

# This is the shorthand log function used in the main thread
def log(x: Any):
    print("\033[96;100mMAIN:\033[0m " + str(x))

# Down here are the actual log parsing functions for actual Log objects
log_prefixes: Dict[str, str] = {
    "MAIN": "\033[100mMAIN:\033[0m ",
    "CTRL": "\033[103mCTRL:\033[0m ",
    "NAV": "\033[104mNAV:\033[0m ",
    "WSKT": "\033[105mWSKT:\033[0m ",
    "LCAL": "\033[106mLOCALIZE:\033[0m ",
    "PRCP": "\033[102mPERCEPT:\033[0m ",
}

def handle_log(message: Log, base_q: Queue) -> Optional[str]:
    print_log: bool = True
    if message.type == "state" and isinstance(message.content, State): 
        print_log = False
        # If type is state, unpack the numpy arrays
        serial_state = SerialState(
            position = message.content.position.tolist(),
            velocity = message.content.velocity.tolist(),
            attitude = message.content.attitude.tolist(),
            angular_velocity = message.content.angular_velocity.tolist(),
        )
        message.content = serial_state.model_dump_json()
    # Since message: Log, we must convert Log to JSON
    result = msgspec.json.encode(message).decode()
    try:
        base_q.put_nowait(result)
    except Full:
        pass
    if print_log:
        print(log_prefixes[message.source] + str(message.content))

def main_log(logging_q: Queue, base_q: Queue) -> None:
    while(logging_q.qsize() > 0):
        try:
            message: Union[Log, str] = logging_q.get_nowait()
            if message:
                #try:
                if isinstance(message, Log):
                    handle_log(message, base_q)
                #except:
                    #print("\033[101mError Handling Log:\033[0m " + repr(message))
        except Empty:
            return 

def motor_test(
    speeds:Tuple[float, float, float, float],
    *,
    motor_controller:AbstractController,
    promises: List[Promise],
    disable_controller: threading.Event,
    time_to_zero: float = 10.0
) -> None:
    """ Safely parse the speeds and dispatch them to the motor controller. Also
        handles disabling any PID control execution while the motor test is
        underway. Also adds a promise to zero the motors after a default of 10
        seconds, which can be customized via `time_to_zero`.
    """
    try:
        disable_controller.set()
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
    subcommand = msg["content"]["sub"]
    if subcommand == "info":
        pass
    elif subcommand == "enable":
        task = tasks[msg["content"]["task"]]
        log("Enabling task: " + task.name)
        task.start()
    elif subcommand == "disable":
        task = tasks[msg["content"]["task"]]
        log("Disabling task: " + task.name)
        task.stop()
    else:
        log("Task manage parsing error")
    response = {}
    for task in tasks:
        response[task.name] = task.started
    log("Task info: \n" + str(response))
    logging_q.put(Log(
        source="MAIN",
        type="important",
        content=msgspec.json.encode(response).decode(),
    ))
