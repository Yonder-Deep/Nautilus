from abc import abstractmethod
from typing import Union
import sys
sys.path.append("../..")
from models.data_types import KinematicState, MotorSpeeds

class AbstractController():
    @abstractmethod
    def set_speeds(self, input:MotorSpeeds):
        pass

    @abstractmethod
    def set_zeros(self):
        pass

    @abstractmethod
    def get_speeds(self) -> MotorSpeeds:
        pass

    @abstractmethod
    def get_state(self) -> Union[KinematicState, None]:
        pass
    
    @abstractmethod
    def set_last_time(self):
        pass
