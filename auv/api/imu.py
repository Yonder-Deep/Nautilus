# Custom imports
import time
import board
from adafruit_lsm6ds import Rate, AccelRange, GyroRange
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX as LSM6DS
from adafruit_lis3mdl import LIS3MDL
import imufusion
import numpy as np
from static import global_vars

class IMU:
    """ Utilize inheritance of the low-level parent class """

    def __init__(self):
        """ Simply call our superclass constructor """
        super().__init__()
        i2c = board.I2C()  # uses board.SCL and board.SDA
        self.ag_sensor = LSM6DS(i2c)
        self.m_sensor = LIS3MDL(i2c)

        self.ag_sensor.accelerometer_range = AccelRange.RANGE_8G
        print(
            "Accelerometer range set to: %d G" % AccelRange.string[self.ag_sensor.accelerometer_range]
        )

        self.ag_sensor.gyro_range = GyroRange.RANGE_2000_DPS
        print("Gyro range set to: %d DPS" % GyroRange.string[self.ag_sensor.gyro_range])

        self.ag_sensor.accelerometer_data_rate = Rate.RATE_1_66K_HZ
        print("Accelerometer rate set to: %d HZ" % Rate.string[self.ag_sensor.accelerometer_data_rate])

        self.ag_sensor.gyro_data_rate = Rate.RATE_1_66K_HZ
        print("Gyro rate set to: %d HZ" % Rate.string[self.ag_sensor.gyro_data_rate])

        self.offset = imufusion.Offset(Rate.RATE_1_66K_HZ)
        self.ahrs = imufusion.Ahrs()

        self.ahrs.settings = imufusion.Settings(
            imufusion.CONVENTION_ENU,  # convention
            0.5,  # gain
            2000,  # gyroscope range
            10,  # acceleration rejection
            10,  # magnetic rejection
            5 * Rate.RATE_1_66K_HZ,  # recovery trigger period = 5 seconds
        )

    def read_euler(self) -> tuple[float, float, float]:
        # Read sensor data
        accel_x, accel_y, accel_z = self.ag_sensor.acceleration
        print(self.ag_sensor.gyro)
        print(global_vars.gyro_offset_vector)

        gyro_x, gyro_y, gyro_z = np.array(self.ag_sensor.gyro) - np.array(global_vars.gyro_offset_vector)
        mag_x, mag_y, mag_z = np.array(self.m_sensor.magnetic) - np.array(global_vars.mag_offset_vector)

        # Update the offset for sensor drift correction
        corrected_gyro_x, corrected_gyro_y, corrected_gyro_z = self.offset.update(np.array([gyro_x, gyro_y, gyro_z]))

        # Update the AHRS algorithm with the sensor data
        self.ahrs.update(
            np.array([corrected_gyro_x, corrected_gyro_y, corrected_gyro_z]),
            np.array([accel_x, accel_y, accel_z]),
            np.array([mag_x, mag_y, mag_z]),
            20.0
        )

        # Get the Euler angles from the AHRS algorithm
        euler_angles = self.ahrs.quaternion.to_euler()

        # Return heading, pitch, and roll
        heading, pitch, roll = euler_angles
        return heading, pitch, roll
