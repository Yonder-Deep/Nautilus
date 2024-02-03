"""Contains test for AUV heading and PID control of heading"""

import threading
from api import PID
from api import Motor
from static import constants
from queue import LifoQueue
import time

# Constants
# Indices for motor array
FORWARD_MOTOR_IDX = 0         # in the back
TURN_MOTOR_IDX = 1            # in the front
FRONT_MOTOR_IDX = 2           # goes up/down
BACK_MOTOR_IDX = 3            # goes up/down

class Heading_Test(threading.Thread):
    """
    Test that makes the AUV point in a certain heading and maintain that heading
    for a certain period of time. Tests the IMU heading data and the PID control
    for heading. 
    """
    def __init__(
        self,
        motor_q,
        halt,
        pressure_sensor,
        imu,
        motors,
        gps,
        gps_q,
        depth_cam,
        in_q,
        out_q,
        heading_pid
    ):
        self.dest_longitude = None
        self.dest_latitude = None
        self.curr_longitude = None
        self.curr_latitude = None
        self.curr_accel = None
        self.motor_q = motor_q
        self.halt = halt
        self.pressure_sensor = pressure_sensor
        self.imu = imu
        self.motors = [Motor(gpio_pin=pin, pi=self.pi)
                       for pin in self.motor_pins]
        self.gps = gps
        self.gps_connected = True if gps is not None else False
        self.gps_q = gps_q
        self.gps_speed_stack = LifoQueue()
        self.depth_cam = depth_cam
        self.in_q = in_q
        self.out_q = out_q
        self.heading_pid = PID(self.mc, 0, 5, 0.1, debug=True, name="Heading", 
                               p=constants.P_HEADING, i=constants.I_HEADING, 
                               d=constants.D_HEADING)

    def update_motor(self) -> None:
        "Update motor speed with PID control input"
        curr_heading, roll, pitch = self.imu.read_euler()
        pid_input = self.heading_pid.pid_heading(curr_heading)
        self.motors[TURN_MOTOR_IDX] += pid_input
    
    def run(self, set_heading=0) -> None:
        "Function that conducts the test"

        self.heading_pid.update_target(set_heading) # set target heading 

        self.motors[FORWARD_MOTOR_IDX] = 0 # reset all motors to 0 speed
        self.motors[TURN_MOTOR_IDX] = 0
        self.motors[BACK_MOTOR_IDX] = 0
        self.motors[FRONT_MOTOR_IDX] = 0

        current_heading, roll, pitch = self.imu.read_euler() # read current heading

        # start the motor at some speed (maybe MAX_SPEED constant)
        self.motors[TURN_MOTOR_IDX] = 1

        if current_heading != 0:
            north = False

        while not north:
            #update_motor()
            #update current_heading
            self.update_motor()
            curr_heading, roll, pitch = self.imu.read_euler() # read current heading
            # check if current_heading is north/0 for 5 seconds. If so, break
            if curr_heading == 0:
                end_time = time.time() + 5
                while time.time() < end_time:
                    self.update_motor()
                new_current_heading, roll, pitch = self.imu.read_euler() 
                if new_current_heading == 0:   
                    north = True 
                    break
        
        # stop motors
        self.motors[TURN_MOTOR_IDX] = 0
        