from models.data_types import KinematicState
from models.shared_memory import write_shared_state
from api.localization import I2C, LSM6DS, LIS3MDL, serial, EKF, MUKF

import multiprocessing
import threading
import queue
from time import time
from typing import Tuple, Callable, Union

import numpy as np

class Localization(multiprocessing.Process):
    def __init__(
        self,
        stop_event: multiprocessing.Event, # type: ignore
        output_shared_memory: str,
        setup_args: Tuple,
        localize_func: Callable[
                [Tuple[I2C, LSM6DS, LIS3MDL, serial.Serial, EKF, MUKF]],
                KinematicState
        ],
    ):
        super().__init__()
        self.stop_event = stop_event
        self.output_shared_memory = output_shared_memory
        self.setup_args = setup_args
        self.localize_func = localize_func

    def run(self):
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

class Mock_Localization(threading.Thread):
    def __init__(
        self,
        stop_event: threading.Event,
        output: str,
        localize_func: Callable[[], Union[KinematicState, None]],
    ):
        super().__init__()
        self.stop_event = stop_event
        self.output = output
        self.localize_func = localize_func

    def run(self):
        while True:
            if self.stop_event.is_set():
                return
            state = self.localize_func()
            if state:
                write_shared_state(name=self.output, state=state)
