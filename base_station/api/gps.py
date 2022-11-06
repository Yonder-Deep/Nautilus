# TODO, someone needs to fix this.

import threading
import time
#import board
#import busio
import serial
import adafruit_gps


class GPS(threading.Thread):
    """ Class for basic GPS functionality """

    def __init__(self, out_queue):
        # Call the threading super-class constructor (inheritance)
        threading.Thread.__init__(self)

        uart = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=10)
        # If using I2C, we'll create an I2C interface to talk to using default pins
        # i2c = board.I2C()
        # Create a GPS module instance.
        self.gps = adafruit_gps.GPS(uart, debug=False)  # Use UART/pyserial
        self.gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
        self.gps.send_command(b"PMTK220,1000")

        self.gps_socket = None
        self.data_stream = None
        self.running = False
        self.out_q = out_queue

        self.start()

    def run(self):

        last_print = time.monotonic()

        # Make sure to call gps.update() every loop iteration and at least twice
        # as fast as data comes from the GPS unit (usually every second).
        # This returns a bool that's true if it parsed new data (you can ignore it
        # though if you don't care and instead look at the has_fix property).
        self.gps.update()
        # Every second print out current location details if there's a fix.
        current = time.monotonic()
        if current - last_print >= 4.0:
            last_print = current
        if not self.gps.has_fix:
            # Try again if we don't have a fix yet.
            print("Waiting for fix...")

            # We have a fix! (gps.has_fix is true)
            # Print out details about the fix like location, date, etc.
            # print("=" * 40)  # Print a separator line.
            # print(
            #     "Fix timestamp: {}/{}/{} {:02}:{:02}:{:02}".format(
            #         self.gps.timestamp_utc.tm_mon,  # Grab parts of the time from the
            #         self.gps.timestamp_utc.tm_mday,  # struct_time object that holds
            #         self.gps.timestamp_utc.tm_year,  # the fix time. Note you might
            #         self.gps.timestamp_utc.tm_hour,  # not get all data like year, day,
            #         self.gps.timestamp_utc.tm_min,  # month!
            #         self.gps.timestamp_utc.tm_sec,
            #     )
            # )
            # print("Latitude: {0:.6f} degrees".format(self.gps.latitude))
            # print("Longitude: {0:.6f} degrees".format(self.gps.longitude))
            # print("Fix quality: {}".format(self.gps.fix_quality))
            # Some attributes beyond latitude, longitude and timestamp are optional
            # and might not be present. Check if they're None before trying to use!
            # if self.gps.satellites is not None:
            #     print("# satellites: {}".format(self.gps.satellites))
            # if self.gps.altitude_m is not None:
            #     print("Altitude: {} meters".format(self.gps.altitude_m))
            # if self.gps.speed_knots is not None:
            #     print("Speed: {} knots".format(self.gps.speed_knots))
            # if self.track_angle_deg is not None:
            #     print("Track angle: {} degrees".format(self.gps.track_angle_deg))
            # if self.horizontal_dilution is not None:
            #     print("Horizontal dilution: {}".format(self.gps.horizontal_dilution))
            # if self.height_geoid is not None:
            #     print("Height geoid: {} meters".format(self.gps.height_geoid))

        self.out_q.put({
            'speed': self.gps.speed_knots,
            'latitude': self.gps.latitude,
            'longitude': self.gps.longitude,
            'altitude': self.gps.altitude_m
        })

        # while (True):
        #     if (self.gps_socket is not None):
        #         self.gps_socket.connect()
        #         self.gps_socket.watch()

        #         for new_data in self.gps_socket:  # Wait for new data on gps socket
        #             if new_data:
        #                 self.data_stream.unpack(new_data)

        #                 # Send gps data (as a dictionary/hashmap) to the synchronous Queue data structure
        #                 self.out_q.push({
        #                     speed: self.data_stream.TPV['speed'],
        #                     latitude: self.data_stream.TPV['lat'],
        #                     longitude: self.data_stream.TPV['lon'],
        #                     altitude: self.data_stream.TPV['alt']
        #                 })

        #     # Sleep for 4 seconds
        #     time.sleep(4)
