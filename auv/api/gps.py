import threading
import time
import serial
import adafruit_gps
import queue
#from static.constants import GPS_PATH

# GPS PATH FOR WINDOWS
# GPS_PATH = 'COM7'
GPS_PATH = '/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0'

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

        while True:

            # Make sure to call gps.update() every loop iteration and at least twice
            # as fast as data comes from the GPS unit (usually every second).
            # This returns a bool that's true if it parsed new data (you can ignore it
            # though if you don't care and instead look at the has_fix property).

            self.gps.update()
            # Every second print out current location details if there's a fix.

            if not self.gps.has_fix:
                self.out_q.put({
                    'has fix': 'No',
                    'speed': 'Unknown',
                    'latitude': 'Unknown',
                    'longitude': 'Unknown'
                })

            else:
                self.out_q.put({
                    'has fix': 'Yes',
                    'speed': self.gps.speed_knots,
                    'latitude': self.gps.latitude,
                    'longitude': self.gps.longitude
                })

            # Every second print out current location details if there's a fix.
            if self.gps.has_fix:
                print("=" * 40)  # Print a separator line.
                print(self.gps.latitude, self.gps.longitude)

            time.sleep(1)


if __name__ == "__main__":

    # Create a queue for the GPS data
    out_q = queue.Queue()

    GPS(out_q)
