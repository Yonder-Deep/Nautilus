from pydantic import BaseModel, Field
from typing import Union
import numpy as np
from numpydantic import NDArray, Shape

# This partial state only has the global position and velocity
class PositionState(BaseModel):
    # Pos-coordinates relative to global origin
    position: Union[NDArray[Shape["3"], np.float64], float] = Field(union_mode='left_to_right')
    # Velocity relative to global origin
    velocity: Union[NDArray[Shape["3"], np.float64], float] = Field(union_mode='left_to_right')

# This state has the rotation, its derivative, 
class State(PositionState):
    local_velocity: Union[NDArray[Shape["3"], np.float64], float] = Field(union_mode='left_to_right')    # Velocity relative to the submarine body
    local_force: Union[NDArray[Shape["3"], np.float64], float] = Field(union_mode='left_to_right')
    attitude: Union[NDArray[Shape["4"], np.float64], float] = Field(union_mode='left_to_right')          # Quaternion: x, y, z, w
    angular_velocity: Union[NDArray[Shape["3"], np.float64], float] = Field(union_mode='left_to_right')
    local_torque:  Union[NDArray[Shape["3"], np.float64], float] = Field(union_mode='left_to_right')

    # These two are included since torque & force will actually be tau_net & F_net
    # and so will include drag forces in addition to motor forces
    forward_m_input: float
    turn_m_input: float

# Complete state required to define the system at any time, including the mass and inertia
class InitialState(State):
    mass: float
    inertia: Union[NDArray[Shape["3, 3"], np.float64], float] = Field(union_mode='left_to_right')

class Log(BaseModel):
    source: str
    type: str
    content: Union[State, str] = Field(union_mode='left_to_right')