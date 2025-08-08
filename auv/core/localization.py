from models.data_types import State, Log, SerialState, logger
from models.shared_memory import write_shared_state
from models.tasks import PTask, TTask

import multiprocessing
import threading
import queue
from time import time
from typing import Tuple, Callable, Union, Literal
from functools import partial

import numpy as np

class Localization(PTask):
    def __init__(
        self,
        logging_q: multiprocessing.Queue,
        output_shared_memory: str,
        setup_args: Tuple,
        kalman_filter: Callable,
        depth_func: Callable[[], float]
    ):
        super().__init__(name="Localization")
        self.output_shared_memory = output_shared_memory
        self.setup_args = setup_args
        self.kalman_filter = kalman_filter
        self.depth_func = depth_func
        self.log = partial(logger, q=logging_q, source="LCAL", verbose=True)

    def run(self):
        meta = self.meta
        self.log("Localization started")
        while True:
            if not meta.started_event.is_set() or not meta.enabled_event.is_set():
                if not meta.enabled_event.is_set():
                    meta.enabled_event.wait()
                if not meta.started_event.is_set():
                    break;
            kf_output = self.kalman_filter()
            output_state = State(
                position=np.array([kf_output.position[0], kf_output.position[1], -self.depth_func()]),
                velocity=np.array([0., 0., 0.]),
                attitude=kf_output["attitude"],
                angular_velocity=kf_output["angular_velocity"],
            )
            write_shared_state(name=self.output_shared_memory, state=output_state)

class Mock_Localization(TTask):
    def __init__(
        self,
        logging_q: queue.Queue,
        output: str,
        localize_func: Callable[[], Union[State, None]],
    ):
        super().__init__(name="Localization")
        self.output = output
        self.logging_q = logging_q
        self.localize_func = localize_func
        self.log = partial(logger, q=logging_q, source="LCAL", verbose=True)

    def run(self):
        meta = self.meta
        self.log("Localization started", source="LCAL")
        while True:
            if not meta.started_event.is_set() or not meta.enabled_event.is_set():
                if not meta.enabled_event.is_set():
                    meta.enabled_event.wait()
                if not meta.started_event.is_set():
                    break;
            state = self.localize_func()
            if state:
                write_shared_state(name=self.output, state=state)
                self.logging_q.put(Log(
                        source="LCAL",
                        type="state",
                        content=SerialState(
                                position=state.position.tolist(),
                                velocity=state.velocity.tolist(),
                                attitude=state.attitude.tolist(),
                                angular_velocity=state.angular_velocity.tolist(),
                        ),
                        dest="BASE",
                ))
