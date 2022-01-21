import threading
import time

from queue import Queue
from . import MotorController

LOOP_SLEEP_DELAY = 0.005


class MotorQueue(threading.Thread):

    def __init__(self, queue):
        self.queue = queue
        self.mc = MotorController()

        self._ev = threading.Event()

        threading.Thread.__init__(self)

    def run(self):

        while not self._ev.wait(timeout=LOOP_SLEEP_DELAY):
            if not self.queue.empty():
                x, y, z = self.queue.get()
                if z == 0:
                    self.run_motors(x, y)
                if z == 1:
                    self.xbox_commands(x, y)

            #time.sleep(LOOP_SLEEP_DELAY)


    def stop(self):
        self._ev.set()


    # for tests only
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

    def xbox_commands(self, x, y):
        x = round(x/100 * 150, 1)
        y = round(y/100 * 150, 1)
        self.mc.update_motor_speeds([y, -x, 0, 0])
