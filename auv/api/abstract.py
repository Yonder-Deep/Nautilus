from abc import abstractmethod
from typing import Union
from custom_types import State, MotorSpeeds

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
    def get_state(self) -> Union[State, None]:
        pass
    
    @abstractmethod
    def set_last_time(self):
        pass
