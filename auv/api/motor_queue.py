import threading
import time

from queue import Queue
from . import MotorController

class MotorQueue(threading.Thread):

    def __init__(self, queue):
        self.queue = queue
        self.mc = MotorController()
        threading.Thread.__init__(self)

    def run(self):

        while True:
            if not self.queue.empty():
                x, y = self.queue.get()
                self.run_motors(x,y)

    def run_motors(self, x, y):
        # stops auv
        self.mc.zero_out_motors()

        forward_speed = 0
        turn_speed = 0

        # turn right
        if (y > 0):
            turn_speed = 90
        # turn left
        elif (y < 0):
            turn_speed = -90

        # turn auv
        self.mc.update_motor_speeds([0, turn_speed, 0, 0])

        # TODO implement so motors run until we've turned y degrees

        time.sleep(5)

        self.mc.zero_out_motors()

        # move forward
        if (x != 0):
            forward_speed = 90
            self.mc.update_motor_speeds([forward_speed, 0, 0, 0])

            # TODO implement so motors run until we've moved x meters
            time.sleep(5)

        self.mc.zero_out_motors()