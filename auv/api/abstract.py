from abc import abstractmethod
from typing import Union
import sys
sys.path.append("../..")
from models.data_types import State, MotorSpeeds

class AbstractController():
    @abstractmethod
    def set_speeds(self, input:MotorSpeeds, verbose=True):
        raise NotImplementedError

    @abstractmethod
    def set_zeros(self):
        raise NotImplementedError

    @abstractmethod
    def get_speeds(self) -> MotorSpeeds:
        raise NotImplementedError

    @abstractmethod
    def get_state(self) -> State:
        raise NotImplementedError
    
    @abstractmethod
    def set_last_time(self):
        raise NotImplementedError
