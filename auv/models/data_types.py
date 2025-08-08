from typing import List, Union, Callable, Optional, Literal
import msgspec

from time import time
from multiprocessing import Queue as MPQueue
from queue import Queue as TQueue

from pydantic import BaseModel, Field, model_validator
import numpy as np

# All in NED global flat earth frame
class State(BaseModel):
    position: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
    velocity: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
    attitude: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
    angular_velocity: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
    
    class Config:
        arbitrary_types_allowed = True

# This state has the rotation, its derivative, 
class ExpandedState(State):
    local_force: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
    local_torque: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))

# Needed because of type stupidity
class SerialState(BaseModel):
    position: List
    velocity: List
    attitude: List
    angular_velocity: List

# Complete state required to define the system at any time, including the mass and inertia
class InitialState(ExpandedState):
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
    source: Literal["MAIN", "CTRL", "NAV", "WSKT", "LCAL", "PRCP"]
    type: str
    content: Union[State, SerialState, dict, str]
    dest: Union[Literal["BASE", "LOG"], str] = "LOG"

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

class Dispatch(msgspec.Struct):
    log: str
    func: Callable

class Cmd(msgspec.Struct):
    command: str
    content: dict

def logger(
    message: str,
    q: Union[TQueue,MPQueue],
    source: Literal["MAIN", "CTRL", "NAV", "WSKT", "LCAL", "PRCP"],
    log_type: str = "info",
    verbose: bool = False,
):
    if verbose and message:
        q.put(Log(
                source = source,
                type = log_type,
                content = message
        ))

