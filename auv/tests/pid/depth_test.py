"""Contains test for AUV depth and PID control of depth"""

import threading
from queue import LifoQueue

# Constants
# Indices for motor array
FORWARD_MOTOR_IDX = 0         # in the back
TURN_MOTOR_IDX = 1            # in the front
FRONT_MOTOR_IDX = 2           # goes up/down
BACK_MOTOR_IDX = 3            # goes up/down

class Depth_Test(threading.Thread):
    """
    Test that makes the AUV point dive a certain distance and maintain that 
    depth for a certain period of time. Tests the IMU depth data and the PID 
    control for depth. 
    """
    def __init__(
        self,
        motor_q,
        halt,
        pressure_sensor,
        imu : IMU,
        motors : list[Motor],
        gps,
        gps_q,
        depth_cam,
        in_q,
        out_q,
        heading_pid : PID
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
                               p=config.P_HEADING, i=config.I_HEADING, 
                               d=config.D_HEADING)
