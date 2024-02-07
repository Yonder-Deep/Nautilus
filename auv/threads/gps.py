import threading
import time
import serial
from static.constants import GPS_PATHS


class GPS(threading.Thread):
    """Class for basic GPS functionality"""

    def __init__(self, out_queue):
        threading.Thread.__init__(self)
        path_found = False
        for gps_path in GPS_PATHS:
            try:
                uart = serial.Serial(gps_path, baudrate=9600, timeout=10)
                path_found = True
                break
            except:
                pass

        if path_found is True:
            return 0
        else:
            raise ("No gps path found.")

    def run(self):
        return 0

    def stop(self):
        self.running = False
