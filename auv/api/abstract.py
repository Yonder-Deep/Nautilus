from typing import Union
import sys
sys.path.append("../..")
from models.data_types import State, MotorSpeeds

class AbstractController():
    def set_speeds(self, input:MotorSpeeds, verbose=True):
        raise NotImplementedError

    def set_zeros(self):
        raise NotImplementedError

    def get_speeds(self) -> MotorSpeeds:
        raise NotImplementedError

    def get_state(self) -> State:
        raise NotImplementedError
    
    def set_last_time(self):
        raise NotImplementedError
