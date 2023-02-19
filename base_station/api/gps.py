import threading
import time
import serial
import adafruit_gps

GPS_PATH = '/dev/serial/by-id/usb-u-blox_AG_-_www.u-blox.com_u-blox_7_-_GPS_GNSS_Receiver-if00'

class GPS(threading.Thread):
    """ Class for basic GPS functionality """

    def __init__(self, out_queue):
        # Call the threading super-class constructor (inheritance)
        threading.Thread.__init__(self)

        uart = serial.Serial(GPS_PATH, baudrate=9600, timeout=10)
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
                'track angle':'Unknown',
                'speed': 'Unknown',
                'latitude': 'Unknown',
                'longitude': 'Unknown'
            })

        else:
            self.out_q.put({
                'has fix':'Yes',
                'track angle':self.gps.track_angle_deg,
                'speed': self.gps.speed_knots,
                'latitude': self.gps.latitude,
                'longitude': self.gps.longitude
            
            })

# Testing area for the GPS class

# if __name__ == "__main__":
#     import queue
#     q = queue.Queue()
#     gps = GPS(q)
#     while True:
#         try:
#             print(q.get())
#             gps.run()
#             time.sleep(0.5)
#         except KeyboardInterrupt:
#             break
    