import threading
import time

class Autonomous_Nav(threading.Thread):
    """ Class for Autonomous Navigation """

    def __init__(self, out_queue):
        self.dest_longitude = None
        self.dest_latitude = None
        self.curr_longitude = None
        self.curr_latitude = None

    def set_destination(self, latitude, longitude):
        self.dest_latitude, self.dest_longitude = latitude, longitude

    def set_curr_position(self, latitude, longitude):
        self.curr_latitude, self.curr_longitude = latitude, longitude

    def run(self, dest_lat, dest_long):
        self.set_destination(dest_lat, dest_long)
        pass