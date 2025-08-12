# Custom imports
import adafruit_bno055 as super_imu
import threading
import time
import board
from math import atan2, sqrt, cos, sin, degrees 
from adafruit_lsm6ds import Rate, AccelRange, GyroRange
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX as LSM6DS
from adafruit_lis3mdl import LIS3MDL
import imufusion
import numpy as np
import config

class IMU():
    """ Utilize inheritance of the low-level parent class """
    
    # Hard iron offset vector
    B = np.array([  -18.49,   46.32,   29.76])
    # Soft iron offset matrix
    Ainv = np.array([[ 32.71410,  0.43184,  0.13793],
             [  0.43184, 38.04931,  0.83862],
             [  0.13793,  0.83862, 29.27600]])

    def __init__(self):
        """ Initialize the IMU sensors and AHRS algorithm """
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
        self.prev_time = time.time()

        self.ahrs = imufusion.Ahrs()

        self.ahrs.settings = imufusion.Settings(
            imufusion.CONVENTION_NWU,  # convention
            0.5,  # gain
            2000,  # gyroscope range
            10,  # acceleration rejection
            10,  # magnetic rejection
            5 * Rate.RATE_1_66K_HZ,  # recovery trigger period = 5 seconds
        )

        # Shared variables with thread safety
        self.heading = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        self.mag_x = self.mag_y = self.mag_z = 0
        self.accel_x = self.accel_y = self.accel_z = 0
        
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = None

    def read_euler(self) -> tuple[float, float, float]:
        """ Return the current heading, pitch, and roll in a thread-safe manner """
        with self.lock:
            return self.roll, self.pitch, self.heading

    def read_compass(self):
        with self.lock:
            ax, ay, az = self.accel_x, self.accel_y, self.accel_z
            mx, my, mz = self.mag_x, self.mag_y, self.mag_z

        theta = atan2(-ax, sqrt(ay * ay + az * az))
        phi = atan2(ay, az)
        x = mx * cos(theta) + my * sin(phi) * sin(theta) + mz * cos(phi) * sin(theta)
        y = my * cos(phi) - mz * sin(phi)

        angle = degrees(atan2(y, x))
        return angle if angle >= 0 else angle + 360

        
    def update_imu_reading(self):
        """ Update IMU readings and compute Euler angles """
        try:
            accel_x, accel_y, accel_z = self.ag_sensor.acceleration
            # print(self.ag_sensor.gyro)
            # print(config.gyro_offset_vector)

            gyro_x, gyro_y, gyro_z = (
                np.array(self.ag_sensor.gyro) - np.array(config.gyro_offset_vector)
            )
            
            mag_x, mag_y, mag_z = np.dot(IMU.Ainv, (np.array(self.m_sensor.magnetic) - IMU.B))

            # Update the offset for sensor drift correction
            corrected_gyro_x, corrected_gyro_y, corrected_gyro_z = self.offset.update(
                np.array([gyro_x, gyro_y, gyro_z])
            )

            new_time = time.time()
            dt = new_time - self.prev_time

            # Update the AHRS algorithm with the sensor data
            self.ahrs.update(
                np.array([corrected_gyro_x, corrected_gyro_y, corrected_gyro_z]),
                np.array([accel_x, accel_y, accel_z]),
                np.array([mag_x, mag_y, mag_z]),
                dt,
            )

            # Get the Euler angles from the AHRS algorithm
            euler_angles = self.ahrs.quaternion.to_euler()

            # Update heading, pitch, and roll in a thread-safe manner
            with self.lock:
                self.roll, self.pitch, self.heading = euler_angles
                self.mag_x, self.mag_y, self.mag_z = mag_x, mag_y, mag_z
                self.accel_x, self.accel_y, self.accel_z = accel_x, accel_y, accel_z
                
            self.prev_time = new_time

        except Exception as e:
            print(f"Error updating IMU readings: {e}")

    def start_reading(self):
        """ Start the sensor reading in a separate thread """
        if self.thread and self.thread.is_alive():
            print("Sensor reading thread is already running.")
            return

        self.thread = threading.Thread(target=self._sensor_reading_loop, daemon=True)
        self.stop_event.clear()
        self.thread.start()
        print("Sensor reading thread started.")

    def stop_reading(self):
        """ Stop the sensor reading thread """
        if self.thread:
            self.stop_event.set()
            self.thread.join()
            print("Sensor reading thread stopped.")

    def _sensor_reading_loop(self):
        """ Continuously update IMU readings """
        while not self.stop_event.is_set():
            self.update_imu_reading()
            time.sleep(0.01)  # Adjust sleep duration as needed
