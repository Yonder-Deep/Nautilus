import threading
import time
import serial
import adafruit_gps
from static.constants import GPS_PATHS

class GPS(threading.Thread):
    """ Class for basic GPS functionality """

    def __init__(self, out_queue):
        # Call the threading super-class constructor (inheritance)
        threading.Thread.__init__(self)

        try:
            for gps_path in GPS_PATHS:
                uart = serial.Serial(gps_path, baudrate=9600, timeout=10)
                break
        except:
            print("GPS not found")
        # If using I2C, we'll create an I2C interface to talk to using default pins
        # i2c = board.I2C()
        # Create a GPS module instance.
        self.gps = adafruit_gps.GPS(uart, debug=False)  # Use UART/pyserial
        self.gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
        self.gps.send_command(b"PMTK220,1000")
        self.out_q = out_queue

        self.run()

    def run(self):

        # Make sure to call gps.update() every loop iteration and at least twice
        # as fast as data comes from the GPS unit (usually every second).
        # This returns a bool that's true if it parsed new data (you can ignore it
        # though if you don't care and instead look at the has_fix property).

        self.gps.update()
        # Every second print out current location details if there's a fix.
        
        if not self.gps.has_fix:
            self.out_q.put({
                'has fix':'No',
                'speed': 'Unknown',
                'latitude': 'Unknown',
                'longitude': 'Unknown'
            })

        else:
            self.out_q.put({
                'has fix':'Yes',
                'speed': self.gps.speed_knots,
                'latitude': self.gps.latitude,
                'longitude': self.gps.longitude
            })