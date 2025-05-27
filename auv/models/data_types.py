from typing import List, Union, Callable, Optional, Literal
import msgspec

import multiprocessing
import multiprocessing.queues
import threading
import queue
from time import time

from pydantic import BaseModel, Field, model_validator
import numpy as np

class KinematicState(BaseModel):
    # All in NED global flat earth frame
    position: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
    velocity: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
    attitude: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
    angular_velocity: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
    
    class Config:
        arbitrary_types_allowed = True

# This state has the rotation, its derivative, 
class State(KinematicState):
    #local_velocity: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
    local_force: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
    local_torque: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))

    # These two are included since torque & force will actually be tau_net & F_net
    # and so will include drag forces in addition to motor forces
    #forward_m_input: float
    #turn_m_input: float

# Needed because of type stupidity
class SerialState(BaseModel):
    position: List
    velocity: List
    #local_velocity: List
    #local_force: List
    attitude: List
    angular_velocity: List
    #local_torque: List
    #forward_m_input: float
    #turn_m_input: float

# Complete state required to define the system at any time, including the mass and inertia
class InitialState(State):
    mass: float
    inertia: np.ndarray = Field(default_factory=lambda: np.zeros((3,3), dtype=float))

class MotorSpeeds(BaseModel):
    forward: float
    turn: float
    front: float
    back: float

    @model_validator(mode='after')
    def valid_speeds(self):
        for speed in [self.forward, self.turn, self.front, self.back]:
            if not -1.0 <= speed <= 1.0:
                raise ValueError('speeds must be from -1.0 to 1.0')
        return self

class Log(msgspec.Struct):
    source: Union[Literal["MAIN"], Literal["PID"], Literal["NAV"], Literal["WSKT"], Literal["LCAL"], Literal["PRCP"], str]
    type: str
    content: Union[KinematicState, State, SerialState, str] = Field(union_mode='left_to_right')

class Promise(msgspec.Struct):
    """ This is a not really a javascript-style "Promise" but is instead a
        simple scheduled callback. If appended to the promises array of the
        main loop, the callback function will be called after the approximate
        time of the duration has elapsed. 
    """
    name: str
    duration: float
    callback: Callable
    init: float = 0.0 # Will be overriden post init by current time

    def __post_init__(self):
        self.init = time()

class GpsData(msgspec.Struct):
    lat: float
    lon: float
    attitude: np.ndarray = Field(default_factory=lambda: np.zeros(4, dtype=float))
