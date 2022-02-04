# not using this file either, refer to xbox.py

import signal
import time
from .xbox import Joystick


class Xbox(Joystick):

    def __init__(self):
        print("attempting superclass")
        super().__init__(0)
        print("superclass did something")

    def leftX(self):
        return self.axis_l.x  # TODO

    def rightTrigger(self):
        return self.trigger_r.value

    def leftTrigger(self):
        return self.trigger_l.value
