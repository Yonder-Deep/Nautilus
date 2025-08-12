from queue import Queue, Empty
from functools import partial

from numpy import array as a
from numpy import float64 as f64

from models.data_types import State, logger
from models.tasks import TTask

class Navigation(TTask):
    """ This top-level navigation thread is meant to take as input
        the current state of the submarine and output what the
        desired state of the submarine is. It is not meant to directly
        control the state of the submarine, merely produce a desired state.
    """
    def __init__(
            self,
            logging_q: Queue,
            desired_state_q: Queue,
            verbose: bool = True,
    ):
        super().__init__(name="Navigation") # For Thread class __init__()
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
        self.desired_state_q = desired_state_q
        self.log = partial(logger, q=logging_q, source="LCAL", verbose=verbose)
    
    def loop(self):
        meta = self.meta
        log = self.log
        try:
            new_input = meta.input_q.get(block=False)
            if new_input:
                log("Navigation sees new input: \n" + str(new_input))

                # No processing here yet, just putting directly into queue

                self.desired_state_q.put(new_input)
        
        except Empty:
            pass
