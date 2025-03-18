from pydantic import BaseModel
import numpy as np
from numpydantic import NDArray, Shape

# This partial state only has the global position and velocity
class PositionState(BaseModel):
    position: NDArray[Shape["3"], np.float64]   # Pos-coordinates relative to global origin
    velocity: NDArray[Shape["3"], np.float64]   # Velocity relative to global origin

# This state has the rotation, its derivative, 
class State(PositionState):
    local_velocity: NDArray[Shape["3"], np.float64]    # Velocity relative to the submarine body
    local_force: NDArray[Shape["3"], np.float64]
    attitude: NDArray[Shape["4"], np.float64]          # Quaternion: x, y, z, w
    angular_velocity: NDArray[Shape["3"], np.float64]
    local_torque:  NDArray[Shape["3"], np.float64]

    # These two are included since torque & force will actually be tau_net & F_net
    # and so will include drag forces in addition to motor forces
    forward_m_input: float
    turn_m_input: float

# Complete state required to define the system at any time, including the mass and inertia
class InitialState(State):
    mass: float
    inertia: NDArray[Shape["3, 3"], np.float64]