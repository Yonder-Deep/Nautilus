from queue import Queue, Empty
from threading import Thread, Event
from functools import partial
from time import sleep

from numpy import array as a
from numpy import float64 as f64
from models.data_types import State, State

def check_verbose(message, q:Queue, verbose:bool=True):
    if verbose:
        q.put("NAV: " + message)

class Navigation(Thread):
    """ This top-level navigation thread is meant to take as input
        the current state of the submarine and output what the
        desired state of the submarine is. It is not meant to directly
        control the state of the submarine, merely produce a desired state.
    """
    def __init__(
            self,
            stop_event:Event,
            input_state_q:Queue,
            desired_state_q:Queue,
            logging_q:Queue,
            verbose:bool=True
    ):
        super().__init__(name="Navigation") # For Thread class __init__()
        self.stop_event = stop_event
        self.input_state = State(
            position = a([0.0, 0.0, 0.0], dtype=f64),
            velocity = a([0.0, 0.0, 0.0], dtype=f64),
            attitude = a([0.0, 0.0, 0.0, 0.0], dtype=f64),
            angular_velocity = a([0.0, 0.0, 0.0], dtype=f64),
        )
        self.desired_state = State(
            position = a([0.0, 0.0, 0.0], dtype=f64),
            velocity = a([0.0, 0.0, 0.0], dtype=f64),
        )
        self.input_state_q = input_state_q
        self.desired_state_q = desired_state_q
        self.log = partial(check_verbose, q=logging_q, verbose=verbose)
    
    def run(self):
        log = self.log
        while not self.stop_event.is_set():
            sleep(1)
            try:
                new_input = self.input_state_q.get(block=False)
                if new_input:
                    log("Navigation sees new input: \n" + str(new_input))
                    # No processing here yet, just putting directly into queue

                    self.desired_state_q.put(new_input)
            
            except Empty:
                pass
