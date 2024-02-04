import threading
import time
import serial
import adafruit_gps
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
            self.gps = adafruit_gps.GPS(uart, debug=False)  # Use UART/pyserial
            self.gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
            self.gps.send_command(b"PMTK220,1000")
            self.out_q = out_queue
            self.running = True
        else:
            raise ("No gps path found.")

    def run(self):
        while self.running is True:
            if not self.gps.has_fix:
                self.out_q.put(
                    {
                        "has fix": "No",
                        "speed": "Unknown",
                        "latitude": "Unknown",
                        "longitude": "Unknown",
                    }
                )
            else:
                self.out_q.put(
                    {
                        "has fix": "Yes",
                        "speed": self.gps.speed_knots,
                        "latitude": self.gps.latitude,
                        "longitude": self.gps.longitude,
                    }
                )

    def stop(self):
        self.running = False
