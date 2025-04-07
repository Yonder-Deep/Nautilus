from typing import Union
from queue import Queue, Empty
from api import MotorController
from threading import Thread, Event
from functools import partial
from time import sleep

from api.mock_controller import MockController
from custom_types import State, PositionState, Log

def check_verbose(message:Union[State,str], q:Queue, verbose:bool):
    if verbose:
        log_type = "info"
        if isinstance(message, State):
            log_type = "state"
        log = Log(
            source = "CTL",
            type = log_type,
            content = message
        )
        q.put(log)

class Control(Thread):
    """ This low-level navigation thread is meant to take as input
        the current state and desired state of the submarine, and
        write to motor controller in order to keep the system
        critically damped so that the error between the current state
        and desired state is minimized.
    """
    def __init__(self, input_state_q:Queue, desired_state_q:Queue, logging_q:Queue, controller:MockController, stop_event:Event):
        super().__init__()
        self.stop_event = stop_event
        self.mc = controller
        self.input_state = State(
            position = [0.0, 0.0, 0.0],
            velocity = [0.0, 0.0, 0.0],
            local_velocity = [0.0, 0.0, 0.0],
            local_force = [0., 0., 0.],
            attitude = [0.0, 0.0, 0.0, 0.],
            angular_velocity = [0.0, 0.0, 0.0],
            local_torque = [0., 0., 0.],
            forward_m_input = 0.0,
            turn_m_input = 0.0
        )
        self.desired_state = PositionState(
            position = [0.0, 0.0, 0.0],
            velocity = [0.0, 0.0, 0.0],
        )
        self.input_state_q = input_state_q
        self.desired_state_q = desired_state_q
        self.log = partial(check_verbose, q=logging_q, verbose=True)
    
    def run(self):
        log = self.log
        log("HELLO")
        self.mc.set_last_time()
        while not self.stop_event.is_set():
            sleep(0.01)
            try:
                new_desired_state = self.desired_state_q.get(block=False)
                if new_desired_state:
                    log("Desired State: \n" + str(new_desired_state))
                    self.desired_state = new_desired_state
                    # No processing here yet, just putting directly into queue
                
            
            except Empty:
                pass

            log(self.mc.get_state())
        # Compare current state & desired state (setpoint), create error value
        # From error value, translate into motor speeds (signal)

    def stop(self):
        """ Probably won't actually use this """
        self.stop_event.set()
        
