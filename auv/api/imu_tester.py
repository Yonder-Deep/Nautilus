from imu import IMU
import time

imu = IMU()
imu.start_reading()
while (True):
    print(imu.read_euler())
    print(imu.read_compass())
    time.sleep(0.5)