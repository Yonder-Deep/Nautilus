from queue import Queue
from api import MotorController
from threading import Thread, Event
from functools import partial

from custom_types import State, PositionState

def check_verbose(message, q=Queue, verbose=bool):
    if verbose:
        q.put("NAV: " + message)

class Control(Thread):
    """ This low-level navigation thread is meant to take as input
        the current state and desired state of the submarine, and
        write to motor controller in order to keep the system
        critically damped so that the error between the current state
        and desired state is minimized.
    """
    def __init__(self, input_state_q=Queue, desired_state_q=Queue, logging_q=Queue, controller=MotorController, stop_event=Event):
        super().__init__()
        self.stop_event = stop_event
        self.mc = controller
        self.input_state = State(
            global_position = [0.0, 0.0, 0.0],
            global_velocity = [0.0, 0.0, 0.0],
            local_velocity = [0.0, 0.0, 0.0],
            attitude = [0.0, 0.0, 0.0],
            angular_velocity = [0.0, 0.0, 0.0],
            forward_m_input = 0.0,
            turn_m_input = 0.0
        )
        self.desired_state = PositionState(
            global_position = [0.0, 0.0, 0.0],
            global_velocity = [0.0, 0.0, 0.0],
        )
        self.input_state_q = input_state_q
        self.desired_state_q = desired_state_q
        self.log = partial(check_verbose, q=logging_q)
    
    def run(self):
        # Compare current state & desired state (setpoint), create error value
        # From error value, translate into motor speeds (signal)
        pass

    