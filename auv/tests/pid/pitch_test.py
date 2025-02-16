"""Contains test for AUV pitch and PID control of pitch"""

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

class Pitch_Test(threading.Thread):
    """
    Test that makes the AUV point in a certain pitch and maintain that pitch
    for a certain period of time. Tests the IMU pitch data and the PID control
    for pitch.
    """

    def __init__(self, imu: IMU, mc: MotorController):
        threading.Thread.__init__(self)
        self.imu = imu
        self.mc = mc
        self.pitch_pid = PID(
            self.mc,
            0, # target
            5, # control tolerance
            5, # target tolerance
            debug=True,
            name="Pitch",
            p=constants.P_PITCH,
            i=constants.I_PITCH,
            d=constants.D_PITCH,
        )

    def update_motor(self, last_speed: float) -> None:
        "Update motor speed with PID control input"
        heading, roll, curr_pitch = self.imu.read_euler()
        print(f"current pitch = {curr_pitch}\n")
        pid_output = self.pitch_pid.pid(curr_pitch, pitch=True)

        self.mc.update_motor_speeds([0, 0, pid_output, -pid_output])

        return pid_output

    def run(self, target_pitch: float = 0) -> None:
        """ Function that conducts the test """
        
        start_time = time.time()

        print(f"Entering run with target_pitch = {target_pitch}")

        self.pitch_pid.update_target(target_pitch)  # set target pitch

        self.mc.update_motor_speeds([0, 0, 0, 0])

        last_speed = 1
        reached_target = False

        while not reached_target:
            # end test after 20 seconds
            if time.time() - start_time > 20:
                break

            last_speed = self.update_motor(last_speed)

        # stop motors
        self.mc.update_motor_speeds([0, 0, 0, 0])