import threading
from typing import Union
from queue import Queue, Empty
from api.abstract import AbstractController
from threading import Thread, Event
from functools import partial
from time import sleep, time
from multiprocessing.shared_memory import SharedMemory

from numpy import array as ar
from numpy import float64 as f64
from scipy.spatial.transform import Rotation as R

from api.mock_controller import MockController
from api.motor_controller import MotorController
from models.data_types import State, KinematicState, Log, MotorSpeeds
from models.shared_memory import read_shared_state

def check_verbose(message:Union[KinematicState,str, None], q:Queue, verbose:bool):
    if verbose and message:
        log_type = "info"
        if isinstance(message, KinematicState):
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
    def __init__(self, input_shared_state:str, desired_state_q:Queue, logging_q:Queue, controller:AbstractController, stop_event:Event, disabled_event:Event):
        super().__init__()
        self.stop_event = stop_event
        self.mc = controller
        self.input_state = State(
            position = ar([0.0, 0.0, 0.0], dtype=f64),
            velocity = ar([0.0, 0.0, 0.0], dtype=f64),
            local_force = ar([0.0, 0.0, 0.0], dtype=f64),
            attitude = ar([0.0, 0.0, 0.0, 0.0], dtype=f64),
            angular_velocity = ar([0.0, 0.0, 0.0], dtype=f64),
            local_torque = ar([0.0, 0.0, 0.0], dtype=f64),
        )
        self.desired_state = 0.0 # Now desired heading only
        """PositionState(
            position = ar([0.0, 0.0, 0.0], dtype=f64),
            velocity = ar([0.0, 0.0, 0.0], dtype=f64),
        )"""
        self.input_shared_state = input_shared_state
        self.desired_state_q = desired_state_q
        self.log = partial(check_verbose, q=logging_q, verbose=True)
        self.disabled_event = disabled_event
        self.last_time = time()
        self._last_err = 0.
        self._integrated = 0.
    
    def run(self):
        log = self.log
        log("HELLO")
        self.mc.set_last_time()
        while not self.stop_event.is_set() and not self.disabled_event.is_set():
            sleep(0.00001)
            try:
                new_desired_state = self.desired_state_q.get_nowait()
                if new_desired_state:
                    log("Desired State: \n" + str(new_desired_state))
                    self.desired_state = new_desired_state
                    # No processing here yet, just putting directly into queue
            
            except Empty:
                pass

            try:
                new_current_state = read_shared_state(name=self.input_shared_state)
                if new_current_state:
                    log(new_current_state)
                    heading_err = self.desired_state - new_current_state.attitude[2] 
                    if heading_err > 180:
                        heading_err -= 360

                    current_time = time()
                    dt = current_time - self.last_time
                    self.last_time = current_time

                    proportional = 0.4 * heading_err
                    self._integrated += heading_err * dt
                    integral = 0.0 * self._integrated
                    derivative = 0.0 * (heading_err - self._last_err) / dt

                    self._last_err = heading_err

                    signal = proportional + integral + derivative
                    final = max(min(signal, 1.0), -1.0)
                    self.mc.set_speeds(MotorSpeeds(
                        forward=0.0,
                        turn=final,
                        front=0.0,
                        back= 0.0
                    ))
                    
            except Empty:
                pass

        # Compare current state & desired state (setpoint), create error value
        # From error value, translate into motor speeds (signal)

    def stop(self):
        """ Probably won't actually use this """
        self.stop_event.set()
    
    def enable(self):
        self.disabled_event.clear()

    def disable(self):
        self.disabled_event.set()
