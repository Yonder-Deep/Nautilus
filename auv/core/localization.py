from models.data_types import KinematicState, Log
from models.shared_memory import write_shared_state

import multiprocessing
import threading
import queue
from time import time
from typing import Tuple, Callable, Union
from functools import partial

import numpy as np

def logger(message: str, q: Union[queue.Queue,multiprocessing.Queue], verbose: bool):
    if verbose and message:
        log_type = "info"
        if isinstance(message, KinematicState):
            log_type = "state"
        q.put(Log(
                source = "LCAL",
                type = log_type,
                content = message
        ))

class Localization(multiprocessing.Process):
    def __init__(
        self,
        stop_event: multiprocessing.Event, # type: ignore
        input_q: multiprocessing.Queue,
        output_shared_memory: str,
        setup_args: Tuple,
        localize_func: Callable[
                ...,
                KinematicState
        ],
    ):
        super().__init__()
        self.stop_event = stop_event
        self.input_q = input_q
        self.output_shared_memory = output_shared_memory
        self.setup_args = setup_args
        self.localize_func = localize_func
        self.log = partial(logger, q=input_q, verbose=True)

    def run(self):
        self.log("Localization started")
        current_time = time()
        while True:
            if self.stop_event.is_set():
                return
            quat, current_time = self.localize_func(current_time, *self.setup_args)
            output_state = KinematicState(
                    position = np.zeros(3, dtype=float),
                    velocity = np.zeros(3, dtype=float),
                    attitude = np.zeros(4, dtype=float),
                    angular_velocity = np.zeros(3, dtype=float),
            )
            write_shared_state(name=self.output_shared_memory, state=output_state)

    def stop(self):
        self.stop_event.set()

class Mock_Localization(threading.Thread):
    def __init__(
        self,
        stop_event: threading.Event,
        input_q: queue.Queue,
        output: str,
        logging_q: queue.Queue,
        localize_func: Callable[[], Union[KinematicState, None]],
    ):
        super().__init__()
        self.stop_event = stop_event
        self.input_q = input_q
        self.output = output
        self.logging_q = logging_q
        self.localize_func = localize_func
        self.log = partial(logger, q=logging_q, verbose=True)

    def run(self):
        self.log("Localization started")
        while True:
            if self.stop_event.is_set():
                return
            state = self.localize_func()
            if state:
                write_shared_state(name=self.output, state=state)
                self.logging_q.put(Log(
                        source="LCAL",
                        type="state",
                        content=state
                ))
