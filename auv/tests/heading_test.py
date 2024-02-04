"""Contains test for AUV heading and PID control of heading"""

import threading
from api import PID
from api import Motor
from api import IMU
from static import constants
import time
from api import MotorController

# Constants
# Indices for motor array
FORWARD_MOTOR_IDX = 0  # in the back
TURN_MOTOR_IDX = 1  # in the front
FRONT_MOTOR_IDX = 2  # goes up/down
BACK_MOTOR_IDX = 3  # goes up/down

# GPIO Pin numbers for Motors
FORWARD_GPIO_PIN = 4
TURN_GPIO_PIN = 11
FRONT_GPIO_PIN = 18
BACK_GPIO_PIN = 24


class Heading_Test(threading.Thread):
    """
    Test that makes the AUV point in a certain heading and maintain that heading
    for a certain period of time. Tests the IMU heading data and the PID control
    for heading.
    """

    def __init__(self):
        self.imu = IMU()
        self.mc = MotorController(), 
        self.motor_pins = [FORWARD_GPIO_PIN, TURN_GPIO_PIN,
        FRONT_GPIO_PIN, BACK_GPIO_PIN]
        self.motors = [Motor(gpio_pin=pin, pi=self.pi) for pin in self.motor_pins]
        self.heading_pid = PID(
            self.mc,
            0,
            5,
            0.1,
            debug=True,
            name="Heading",
            p=constants.P_HEADING,
            i=constants.I_HEADING,
            d=constants.D_HEADING,
        )

    def update_motor(self, last_speed: float) -> None:
        "Update motor speed with PID control input"
        curr_heading, roll, pitch = self.imu.read_euler()
        pid_input = self.heading_pid.pid_heading(curr_heading)

        self.mc.update_motor_speeds([0,last_speed + pid_input,0,0])

        return last_speed + pid_input
        #self.motors[TURN_MOTOR_IDX] += pid_input

    def run(self, target_heading: float = 0) -> None:
        "Function that conducts the test"

        start_time = time.time()

        print(f"Entering run with target_heading = {target_heading}")

        self.heading_pid.update_target(target_heading)  # set target heading

        self.motors[FORWARD_MOTOR_IDX].set_speed(0)  # reset all motors to 0 speed
        self.motors[TURN_MOTOR_IDX].set_speed(0)
        self.motors[BACK_MOTOR_IDX].set_speed(0)
        self.motors[FRONT_MOTOR_IDX].set_speed(0)

        curr_heading, roll, pitch = self.imu.read_euler()  # read current heading

        # start the motor at some speed (maybe MAX_SPEED constant)
        self.motors[TURN_MOTOR_IDX].set_speed(1)
        last_speed = 1

        if curr_heading != target_heading:
            reached_target = False

        while not reached_target:
            if time.time() - start_time > 10:
                self.motors[FORWARD_MOTOR_IDX].set_speed(0)  # reset all motors to 0 speed
                self.motors[TURN_MOTOR_IDX].set_speed(0)
                self.motors[BACK_MOTOR_IDX].set_speed(0)
                self.motors[FRONT_MOTOR_IDX].set_speed(0)
                break 

            # update_motor()
            # update current_heading
            last_speed = self.update_motor(last_speed)
            curr_heading, roll, pitch = self.imu.read_euler()  # read current heading
            # check if current_heading is north/0 for 5 seconds. If so, break

            if curr_heading == target_heading:
                end_time = time.time() + 5
                while time.time() < end_time:
                    last_speed = self.update_motor(last_speed)
                new_current_heading, roll, pitch = self.imu.read_euler()

                if abs(new_current_heading - target_heading) < 0.001:
                    reached_target = True
                    break

        # stop motors
        self.motors[TURN_MOTOR_IDX].set_speed(0)
