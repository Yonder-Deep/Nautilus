""" The main functions for the main __init__ thread, to react to commands from
    base and oversee general instructions for the other threads.
"""

from typing import Tuple, List, Union
from queue import Queue, Empty
import threading
from time import time

from api.abstract import AbstractController
from models.data_types import Promise, MotorSpeeds, Log, State, SerialState

def main_log(logging_queue:Queue, base_queue:Queue):
    thing = 0
    while(logging_queue.qsize() > 0):
        try:
            thing += 1
            message: Union[Log,str] = logging_queue.get_nowait()
            if message:
                if isinstance(message, Log): # If it is just a string, do nothing
                    if message.type == "state" and isinstance(message.content, State): 
                        # If type is state, unpack the numpy arrays
                        serial_state = SerialState(
                            position = message.content.position.tolist(),
                            velocity = message.content.velocity.tolist(),
                            #local_velocity = message.content.local_velocity.tolist(),
                            local_force = message.content.local_force.tolist(),
                            attitude = message.content.attitude.tolist(),
                            angular_velocity = message.content.angular_velocity.tolist(),
                            local_torque = message.content.local_force.tolist(),
                            #forward_m_input = float(message.content.forward_m_input),
                            #turn_m_input = float(message.content.turn_m_input)
                        )
                        message.content = serial_state
                    # Since message: Log, we must convert Log to JSON
                    message = message.model_dump_json()
                base_queue.put(message)
                print("LOG: " + str(message))
        except Empty:
            return  

def motor_test(
    motor_controller:AbstractController,
    speeds:Tuple[float, float, float, float],
    *,
    promises: List[Promise],
    disable_controller: threading.Event,
):
    try:
        disable_controller.set()
        motor_speeds = MotorSpeeds(
            forward = speeds[0],
            turn = speeds[1],
            front = speeds[2],
            back = speeds[3],
        )
        motor_controller.set_speeds(motor_speeds)
        print("Set motor speeds: " + motor_speeds.model_dump_json())
    except ValueError as e:
        print("Motor speeds invalid: " + str(speeds))
        print(e)
    finally:
        noExistingPromise = True 
        for promise in promises:
            if promise.name=="motorReset":
                promise.init = time()
                noExistingPromise = False 
                print("Mutated existing motor reset promise")
        if noExistingPromise: 
            promises.append(Promise(
                name="motorReset",
                duration = 10,
                callback = lambda: motor_controller.set_zeros()
            ))
            print("Appended motor reset promise")
