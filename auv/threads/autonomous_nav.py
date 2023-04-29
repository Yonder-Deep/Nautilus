import threading
import time

class Autonomous_Nav(threading.Thread):
    """ Class for Autonomous Navigation """

    def __init__(self, motor_q, halt, pressure_sensor, imu, mc, gps, gps_q, depth_cam, in_q, out_q):
        self.dest_longitude = None
        self.dest_latitude = None
        self.curr_longitude = None
        self.curr_latitude = None
        self.motor_q = motor_q
        self.halt = halt
        self.pressure_sensor = pressure_sensor
        self.imu = imu
        self.mc = mc
        self.gps = gps
        self.gps_q = gps_q
        self.depth_cam = depth_cam
        self.in_q = in_q
        self.out_q = out_q

    def set_destination(self, latitude, longitude):
        self.dest_latitude, self.dest_longitude = latitude, longitude

    def set_curr_position(self, latitude, longitude):
        self.curr_latitude, self.curr_longitude = latitude, longitude

    def path_find(self):
        searching = True
        direction_flag = 0
        while(searching):
            if direction_flag == 0:
                if True:
                    break
                else:
                    direction_flag = 1
                    continue
            elif direction_flag == 1:
                if True:
                    break
                else:
                    direction_flag = 0
                    continue
            if True:
                searching = False

    def run(self, dest_lat, dest_long):
        self.set_destination(dest_lat, dest_long)
        pass