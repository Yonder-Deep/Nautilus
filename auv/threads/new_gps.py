import threading
import time
import serial
import string
import pynmea2
from static.constants import GPS_PATHS


class GPS(threading.Thread):
    """Class for basic GPS functionality"""

    def __init__(self, out_queue):
        threading.Thread.__init__(self)
        path_found = False
        for gps_path in GPS_PATHS:
            try:
                ser = serial.Serial(gps_path, baudrate=9600, timeout=10)
                path_found = True
                break
            except:
                pass

        if path_found is True:
            dataout = pynmea2.NMEAStreamReader()
            newdata = ser.readline()
            if '$GPRMC' in str(newdata):
                print(newdata.decode('utf-8'))
                newmsg = pynmea2.parse(newdata.decode('utf-8'))
                lat = newmsg.latitude
                lng = newmsg.longitude
                gps = "Latitude" + str(lat) + "and Longitude=" + str(lng)

                self.gps = gps
                self.out_q = out_queue

                self.running = True
        else:
            self.running = False
            raise ("No gps path found.")

    def run(self):
        while self.running is True:
            print(self.gps.has_fix)
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
            time.sleep(1)

    def stop(self):
        self.running = False
