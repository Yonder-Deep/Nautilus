from typing import Union
from queue import Queue, Empty
from functools import partial
from time import sleep, time

import numpy as np
from numpy import array as ar, float64 as f64

from api.abstract import AbstractController
from models.data_types import State, Log, MotorSpeeds, logger
from models.shared_memory import read_shared_state
from models.tasks import TTask

def sigmoid(x):
    """ Maps from input of all real numbers to output between 0 and 1
    """
    return 1 / (1 + np.exp(-x))

class Control(TTask):
    """ This low-level navigation thread is meant to take as input the current
        state and desired state of the submarine, and write to motor controller
        in order to keep the system critically damped so that the error between
        the current state and desired state is minimized.
    """
    def __init__(
            self, 
            shared_state_name: str, 
            logging_q: Queue, 
            controller: AbstractController, 
    ):
        super().__init__(name="Control")
        self.shared_state_name = shared_state_name 
        self.mc = controller
        self.estimated_state = read_shared_state(name=shared_state_name)
        self.desired_state = State(
                position = ar([10.0, 0.0, 10.0], dtype=f64),
                velocity = ar([0.0, 0.0, 0.0], dtype=f64),
                attitude = ar([0.0, 0.0, 50.0], dtype=f64),
                angular_velocity = ar([0.0, 0.0, 0.0], dtype=f64),
        )
        self.log = partial(logger, q=logging_q, source="CTRL", verbose=True)
        self._last_time = time()
        self._last_err = 0.
        self._integral = np.zeros(6, dtype=f64)
        self.thrust_allocation = np.linalg.pinv(np.array([
                [ 1, 0, 0, 0],
                [ 0, 0, 0, 0],
                [ 0, 0, 0.5, 0.5],
                [ 0, 0, 0, 0],
                [ 0, 0, -1, 1],
                [ 0, 1, 0, 0],
        ]))
        self.Kp = ar([0.5, 0.5, 0.5, 0., 0., 0.5])
        self.Ki = ar([0.05, 0.05, 0.05, 0., 0., 0.0])
        self.Kd = ar([0., 0., 0., 0., 0., 0.1])
    
    def run(self):
        meta = self.meta
        log = self.log
        log("Control alive")
        mc = self.mc
        mc.set_last_time()
        while True:
            if not meta.started_event.is_set() or not meta.enabled_event.is_set():
                if not meta.enabled_event.is_set():
                    meta.enabled_event.wait()
                if not meta.started_event.is_set():
                    break;
            sleep(0.0001)
            try:
                msg = meta.input_q.get_nowait()
                if msg:
                    log("Control input received")
                    try:
                        if msg["command"] == "control":
                            log("Desired State: " + str(msg["content"]))
                            self.desired_state.position = msg["content"].position
                            self.desired_state.attitude = msg["content"].attitude
                        elif msg["command"] == "pid":
                            log("PID constants changed: " + str(msg["content"]))
                            indices = ["surge", "sway", "heave", "roll", "pitch", "yaw"]
                            index = indices.index(msg["content"]["axis"])
                            self.Kp[index] = msg["content"]["p"]
                            self.Ki[index] = msg["content"]["i"]
                            self.Kd[index] = msg["content"]["d"]
                    except:
                        log("Control input failed to parse")
            except Empty:
                pass

            try:
                self.estimated_state: State = read_shared_state(name=self.shared_state_name)
                if self.estimated_state:
                    setpoint = np.concatenate((self.desired_state.position, self.desired_state.attitude))
                    estimated = np.concatenate((self.estimated_state.position, self.estimated_state.attitude))
                    err = setpoint - estimated

                    # Solves wrap-around angle problem
                    err[3] = (err[3] + 540) % 360 - 180
                    err[4] = (err[4] + 540) % 360 - 180
                    err[5] = (err[5] + 540) % 360 - 180

                    current_time = time()
                    dt = current_time - self._last_time
                    self._last_time = current_time

                    self._integral += err * dt
                    integral = np.maximum(np.minimum(self._integral, 1) ,-1)
                    derivative = (err - self._last_err) / dt
                    self._last_err = err

                    signal = self.Kp * err + self.Ki * integral + self.Kd * derivative
                    # Thruster allocation with final values between 0 and 1
                    speeds = np.maximum(np.minimum(np.dot(self.thrust_allocation, signal), 1), -1)
                    log("ERR: " + str(err.round(2)))
                    #log("SGL: " + str(signal.round(2)))
                    #log("SPD: " + str(speeds))
                    self.mc.set_speeds(MotorSpeeds(
                        forward=speeds[0],
                        turn=speeds[1],
                        front=speeds[2],
                        back=speeds[3],
                    ),
                    )
            except Empty:
                pass
