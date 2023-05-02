import threading
import time
import math
import pyproj


class Autonomous_Nav(threading.Thread):
    """ Class for Autonomous Navigation """

    def __init__(self, motor_q, halt, pressure_sensor, imu, mc, gps, gps_q, depth_cam, in_q, out_q):
        self.dest_longitude = None
        self.dest_latitude = None
        self.curr_longitude = None
        self.curr_latitude = None
        self.curr_gps_speed = None
        self.motor_q = motor_q
        self.halt = halt
        self.pressure_sensor = pressure_sensor
        self.imu = imu
        self.mc = mc
        self.gps = gps
        self.gps_connected = True if gps is not None else False
        self.gps_q = gps_q
        self.depth_cam = depth_cam
        self.in_q = in_q
        self.out_q = out_q

    def set_destination(self, latitude, longitude):
        self.dest_latitude, self.dest_longitude = latitude, longitude

    def retrieve_curr_position(self):
        # We are assuming gps is already conencted
        self.gps.run()
        gps_data = self.gps_q.get()
        if gps_data['has fix'] == 'Yes':
            latitude = gps_data['latitude']
            longitude = gps_data['longitude']
            speed = gps_data['speed']
            latitude = round(latitude, 6)
            longitude = round(longitude, 6)
            speed = round(speed, 6)
            self.curr_latitude = latitude
            self.curr_longitude = longitude
            self.curr_gps_speed = speed
        else:
            pass  # TODO we need to figure out what to do when the GPS does not have a fix

    def distance_calc(self, lat1, lon1, lat2, lon2):
        # Set up the pyproj Geod object using the WGS-84 ellipsoid
        geod = pyproj.Geod(ellps='WGS84')

        # Calculate the geodetic distance and azimuth between the two points
        geodetic_dist, azimuth1, azimuth2 = geod.inv(lon1, lat1, lon2, lat2)

        # Calculate the horizontal and vertical distances using the geodetic distance and azimuth
        vert_dist = abs(lat2 - lat1) * 111132.954  # Average meridional radius of curvature of the Earth
        horiz_dist = geodetic_dist * abs(math.cos(math.radians((lat2 + lat1) / 2.0))) * 111319.9

        # Print the geodetic distance, horizontal distance, and vertical distance
        print(f'Geodetic distance: {geodetic_dist:.6f} meters')
        print(f'Horizontal distance: {horiz_dist:.6f} meters')
        print(f'Vertical distance: {vert_dist:.6f} meters')

        return geodetic_dist, vert_dist, horiz_dist

    def obstacle_path_find(self):
        searching = True
        direction_flag = 0
        while (searching):
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
        if self.gps_connected == True:
            self.set_destination(dest_lat, dest_long)
            self.retrieve_curr_position()
            # self.imu.read_euler() idk what to do about the imu. does this branch even have the most recent code? a queue would be best
            pass
        else:
            exit()
