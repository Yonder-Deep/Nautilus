from pydantic import BaseModel
import numpy as np
from numpydantic import NDArray, Shape

class PositionState(BaseModel):
    global_position: NDArray[Shape["3"], np.float64]   # Pos-coordinates relative to global origin
    global_velocity: NDArray[Shape["3"], np.float64]   # Velocity relative to global origin

class State(PositionState):
    local_velocity: NDArray[Shape["3"], np.float64]    # Velocity relative to the submarine body
    attitude: NDArray[Shape["3"], np.float64]          # Euler 3-2-1 relative to N frame
    angular_velocity: NDArray[Shape["3"], np.float64]  # WIP
    forward_m_input: float
    turn_m_input: float