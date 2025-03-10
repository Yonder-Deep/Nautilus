"""
basic_quaternion.py

Very basic kalman filter based on the quaternion kinematics equation. This 
filter treats nonlinear equations using the standard kalman process but 
"linearizes" them using a first degree polynomial.
"""

import threading
import time
from math import atan2, sqrt, cos, sin, degrees

import board
import numpy as np
from scipy.spatial.transform import Rotation
from adafruit_lis3mdl import LIS3MDL
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX as LSM6DS

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

        self.prev_time = time.time()

        # Shared variables with thread safety
        self.x = np.array([1, 0, 0, 0])
        self.P = 4 * np.eye(4)
        self.wx = self.wy = self.wz = 0

        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = None

    def read_euler(self) -> tuple[float, float, float]:
        """ Return the current heading, pitch, and roll in a thread-safe manner """
        with self.lock:
            yaw, pitch, roll = Rotation.from_quat(self.x).as_euler("ZYX", degrees=True)
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
        
    def apply_low_pass_filter(self, accel_raw, dt):
        """ Apply the high-pass filter to the gyroscope data """
        low_pass_cutoff_freq = 0.1
        alpha = 0
        with self.lock:
            filtered = alpha * (self.filtered_gyro + gyro_raw - self.prev_gyro)
            self.filtered_gyro = filtered
            self.prev_gyro = gyro_raw
            return filtered
    
    def update_imu_reading(self):
        """ Update IMU readings and compute Euler angles """
        try:
            new_time = time.time()
            dt = new_time - self.prev_time

            # Read data from sensor(s)
            ax, ay, az = self.ag_sensor.acceleration
            wx, wy, wz = self.apply_high_pass_filter(self.ag_sensor.gyro)
            mx, my, mz = IMU.Ainv @ (np.array(self.m_sensor.magnetic) - IMU.B)

            """Predict"""
            # Process noise
            Q = 0.005 * np.eye(4)

            # Quaternion kinematics equation
            omega = np.array([
                [0, -wx, -wy, -wz],
                [wx, 0, wz, -wy],
                [wy, -wz, 0, wx],
                [wz, wy, -wx, 0]
            ])
            F = (np.eye(4) + dt * 0.5 * omega)

            # Predict state and covariance
            with self.lock:
                x_p = F @ self.x
                P_p = F @ self.P @ F.T + Q

            """Update"""
            # State to measurement matrix
            H = np.eye(4)

            # Measurement noise
            R = 1 * np.eye(4)
            
            # Calculate measurement
            phi = atan2(ay, az)
            theta = atan2(-ax, sqrt(ay * ay + az * az))
            psi = atan2(mx * cos(theta) + my * sin(phi) * sin(theta) + mz * cos(phi) * sin(theta),
                        my * cos(phi) - mz * sin(phi))
            z = Rotation.from_euler('ZYX', [psi, theta, phi]).as_quat()

            # Calculate residual
            y = (z - H @ x_p)

            # Kalman gain
            S = H @ P_p @ H.T + R
            K = P_p @ H.T @ np.linalg.inv(S)

            # Update state and covariance estimate
            x = x_p + K @ y
            P = (np.eye(4) - K @ H) @ P_p

            # Update heading, pitch, and roll in a thread-safe manner
            with self.lock:
                self.x = x
                self.P = P

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