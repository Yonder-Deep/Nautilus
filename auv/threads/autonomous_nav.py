import os
import threading
import time
import math
import numpy as np
import pyproj
from queue import Queue
from queue import LifoQueue

from auv.static import constants


class Autonomous_Nav(threading.Thread):
    """Class for Autonomous Navigation"""

    def __init__(
        self,
        motor_q,
        halt,
        pressure_sensor,
        imu,
        mc,
        gps,
        gps_q,
        depth_cam,
        in_q,
        out_q,
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
        self.mc = mc
        self.gps = gps
        self.gps_connected = True if gps is not None else False
        self.gps_q = gps_q
        self.gps_speed_stack = LifoQueue()
        self.depth_cam = depth_cam
        self.in_q = in_q
        self.out_q = out_q

    def set_destination(self, latitude, longitude):
        self.dest_latitude, self.dest_longitude = latitude, longitude

    def retrieve_curr_position(self):
        # We are assuming gps is already connected
        gps_data = self.gps_q.get()
        if gps_data["has fix"] == "Yes":
            latitude = gps_data["latitude"]
            longitude = gps_data["longitude"]
            speed = gps_data["speed"]
            latitude = round(latitude, 6)
            longitude = round(longitude, 6)
            speed = round(speed, 6)
            self.curr_latitude = latitude
            self.curr_longitude = longitude
            self.curr_gps_speed = speed
        else:
            self.stop_motors()

    def distance_calc(self, lat1, lon1, lat2, lon2):
        # Set up the pyproj Geod object using the WGS-84 ellipsoid
        geod = pyproj.Geod(ellps="WGS84")

        # Calculate the geodetic distance and azimuth between the two points
        geodetic_dist, azimuth1, azimuth2 = geod.inv(lon1, lat1, lon2, lat2)

        # Calculate the horizontal and vertical distances using the geodetic distance and azimuth
        vert_dist = (
            abs(lat2 - lat1) * 111132.954
        )  # Average meridional radius of curvature of the Earth
        horiz_dist = (
            geodetic_dist * abs(math.cos(math.radians((lat2 + lat1) / 2.0))) * 111319.9
        )

        # Print the geodetic distance, horizontal distance, and vertical distance
        print(f"Geodetic distance: {geodetic_dist:.6f} meters")
        print(f"Horizontal distance: 
              {horiz_dist:.6f} meters")
        print(f"Vertical distance: {vert_dist:.6f} meters")

        return geodetic_dist, vert_dist, horiz_dist

    def update_movement(self):
        speed1 = (
            self.gps_speed_stack.get()
        )  # these will be important for adjusting thrust to reach omptimum speed
        speed2 = self.gps_speed_stack.get()
        speed3 = self.gps_speed_stack.get()
        speed4 = self.gps_speed_stack.get()

        geod_dist, vert_dist, horiz_dist = self.distance_calc(
            self.curr_latitude,
            self.curr_longitude,
            self.dest_latitude,
            self.dest_longitude,
        )
        angle = np.arctan(vert_dist / horiz_dist)
        diag_dist = math.sqrt(pow(horiz_dist, 2) + pow(vert_dist, 2))

    def obstacle_path_find(self):
        searching = True
        direction_flag = 0
        while searching:
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

    def dive(self, to_depth, depth_time):
        self.diving = True
        # Check if this path is actually right
        file_path = (
            os.path.dirname(os.path.dirname(__file__)) + "logs/" + constants.DIVE_LOG
        )
        log_file = open(file_path, "a")
        self.dive_log(log_file)

        self.motor_queue.queue.clear()

        # begin dive
        self.dive_controller.start_dive(to_depth=to_depth, dive_length=depth_time)

        # resurface
        self.dive_controller.start_dive()

        self.diving = False
        log_file.close()

    def run(self, dest_lat, dest_long, depth, time):
        """Main loop for autonomous nav"""
        # Travelling to destination
        if self.gps_connected == True:
            reached_destination = False
            self.set_destination(dest_lat, dest_long)

            """ Navigating to destination autonomously """
            while reached_destination == False:
                time.sleep(0.5)
                # TODO: Check if here is an obstacle- if true: apply path finding algo , IF NOT, CONTINUE WITH THE STEPS BELOW

                self.retrieve_curr_position()
                self.mc.update_motor_speeds()

                if self.curr_latitude == dest_lat and self.curr_longitude == dest_long:
                    reached_destination = True

            """ Diving autonomously """
            self.dive(depth, time)

        else:
            # Add a print statement? or a message to the console?
            exit()

    