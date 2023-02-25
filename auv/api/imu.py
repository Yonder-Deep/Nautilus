# Custom imports
from Adafruit_BNO055.BNO055 import BNO055 as super_imu
import time


class IMU(super_imu):
    """ Utilize inheritance of the low-level parent class """

    def __init__(self, serial_port, rst):
        """ Simply call our superclass constructor """
        super().__init__()
        error_count = 0
        while error_count < 20:
            try:
                begun = super().begin()
                break
            except:
                print("BNO didn't initialize. Retrying...")
                error_count += 1
                time.sleep(0.2)

        if error_count == 20:
            raise RuntimeError("Failed to initialize BNO055! Is the sensor connected correctly?")

    def read_euler(self):

        # Read the Euler angles for heading, roll, pitch (all in degrees).
        heading, roll, pitch = super().read_euler()

        return heading, roll, pitch
