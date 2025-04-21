from re import L
from pydantic import BaseModel, Field
from typing import List, Union
import numpy as np

# This partial state only has the global position and velocity
class PositionState(BaseModel):
    # Pos-coordinates relative to global origin
    position: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
    # Velocity relative to global origin
    velocity: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
    
    class Config:
        arbitrary_types_allowed = True

# This state has the rotation, its derivative, 
class State(PositionState):
    #local_velocity: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
    local_force: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
    attitude: np.ndarray = Field(default_factory=lambda: np.zeros((3,3), dtype=float)) # Quaternion: x, y, z, w
    angular_velocity: np.ndarray = Field(default_factory=lambda: np.zeros(3, dtype=float))
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
    local_force: List
    attitude: List
    angular_velocity: List
    local_torque: List
    #forward_m_input: float
    #turn_m_input: float

# Complete state required to define the system at any time, including the mass and inertia
class InitialState(State):
    mass: float
    inertia: np.ndarray = Field(default_factory=lambda: np.zeros((3,3), dtype=float))

class Log(BaseModel):
    source: str
    type: str
    content: Union[State, SerialState, str] = Field(union_mode='left_to_right')
