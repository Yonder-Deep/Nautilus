# Custom imports
import serial
from Adafruit_BNO055.BNO055 import BNO055 as super_imu
IMU_RESET_PIN = 8


class IMU(super_imu):
    """ Utilize inheritance of the low-level parent class """

    def __init__(self, path):
        """ Simply call our superclass constructor """
        super().__init__(serial.Serial(path), rst=IMU_RESET_PIN)
    # TODO Implement more useful functions other than the default
