"""
imu_test.py

Code to test the IMU with different Kalman Filters
"""

import threading
import time

import board
import numpy as np
from scipy.spatial.transform import Rotation
from adafruit_lis3mdl import LIS3MDL
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX as LSM6DS

from unscented_quat import MUKF

class IMU:
    # Hard iron offset vector
    B = np.array([-18.49, 46.32, 29.76])
    # Soft iron offset matrix
    Ainv = np.array([[32.71410, 0.43184, 0.13793],
                     [0.43184, 38.04931,  0.83862],
                     [0.13793,  0.83862, 29.27600]])

    def __init__(self):
        super().__init__()
        i2c = board.I2C()  # uses board.SCL and board.SDA
        self.ag_sensor = LSM6DS(i2c)
        self.m_sensor = LIS3MDL(i2c)
        # Set Filter
        self.filter = MUKF()

        self.prev_time = time.time()

        # Shared variables with thread safety
        self.q = np.array([1.0, 0.0, 0.0, 0.0])

        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = None

    def read_euler(self) -> tuple[float, float, float]:
        """ 
        Return the current heading, pitch, and roll in a thread-safe manner 
        """
        with self.lock:
            yaw, pitch, roll = Rotation.from_quat(self.q).as_euler("ZYX", degrees=True)
            return yaw, pitch, roll
    
    def apply_high_pass_filter(self, gyro_raw, dt):
        """ Apply the high-pass filter to the gyroscope data """
        high_pass_cutoff_freq = 0
        alpha = 1 / (2 * np.pi * dt * high_pass_cutoff_freq + 1)
        with self.lock:
            filtered = alpha * (self.filtered_gyro + gyro_raw - self.prev_gyro)
            self.filtered_gyro = filtered
            self.prev_gyro = gyro_raw
            return filtered
        
    def apply_low_pass_filter(self, gyro_raw, dt):
        """ Apply the high-pass filter to the gyroscope data """
        low_pass_cutoff_freq = 0.1
        alpha = 0
        with self.lock:
            filtered = alpha * (self.filtered_gyro + gyro_raw - self.prev_gyro)
            self.filtered_gyro = filtered
            self.prev_gyro = gyro_raw
            return filtered
    
    def update_imu_reading(self):
        """ Reads sensor data and updates estimated state """
        try:
            new_time = time.time()
            dt = new_time - self.prev_time

            # Read data from sensor(s)
            am = np.array(self.ag_sensor.acceleration)
            wm = np.array(self.apply_high_pass_filter(self.ag_sensor.gyro, dt))
            mm = np.array(IMU.Ainv @ (np.array(self.m_sensor.magnetic) - IMU.B))
            
            self.filter.update_imu(am, wm, mm, dt)

            self.prev_time = new_time
            
            with self.lock:
                self.q = self.filter.get_current_orientation()

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
