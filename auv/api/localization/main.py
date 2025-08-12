import serial
import pynmea2
import board
from busio import I2C
import time
import math
import numpy as np
from typing import Callable

from adafruit_lis3mdl import LIS3MDL
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX as LSM6DS
from scipy.spatial.transform import Rotation

from extended_filter import EKF, ImuData, GpsCoordinate, GpsVelocity
from models.data_types import KinematicState
from unscented_quat import MUKF

# --- magnetometer calibration constants ---
B = np.array([  -10.37,   67.69,   72.69])

Ainv = np.array([[ 23.53008,  0.22607, -0.41871],
            [  0.22607, 26.72366, -0.43045],
            [ -0.41871, -0.43045, 21.73834]])

def parse_gprmc(sentence):
    msg = pynmea2.parse(sentence)
    if getattr(msg, "status", None) != 'A':
        return None
    return msg.latitude, msg.longitude, msg.spd_over_grnd, msg.true_course

def heading_to_ned(speed_kt, course_deg):
    speed_ms = speed_kt * 0.514444
    rad = math.radians(course_deg) if course_deg is not None else 0.0
    v_n = speed_ms * math.cos(rad)
    v_e = speed_ms * math.sin(rad)
    return v_n, v_e

def localize_setup(): # Temporary for instatiation
    # I²C sensors
    i2c       = board.I2C()
    ag_sensor = LSM6DS(i2c)
    m_sensor  = LIS3MDL(i2c)

    # GPS serial
    ser = serial.Serial("/dev/tty0", baudrate=9600, timeout=1)

    ekf = EKF()
    mukf = MUKF()

    return i2c, ag_sensor, m_sensor, ser, ekf, mukf

def localize(
    prev_time: float,
    i2c: I2C,
    ag_sensor: LSM6DS,
    m_sensor: LIS3MDL,
    ser: serial.Serial,
    ekf: EKF,
    mukf: MUKF,
) -> KinematicState:
    cur_time = time.time()
    dt = cur_time - prev_time
         
    # --- read IMU & mag ---
    am = np.array(ag_sensor.acceleration)
    wm = np.array(ag_sensor.gyro)
    mm = np.array(Ainv @ (np.array(m_sensor.magnetic) - B))
    
    mukf.update_imu(dt, am, wm, mm)
    q = mukf.get_current_orientation()

    imu = ImuData(accX=am[0], accY=am[1], accZ=am[2])
    
    ekf.predict(dt, imu, q)
    line = ser.readline()
    if line.startswith(b'$GPRMC'):
        s = line.decode('utf-8').strip()
        parsed = parse_gprmc(s)
        print(parsed)
        if parsed:
            lat_deg, lon_deg, spd_kt, crs_deg = parsed
            lat_rad = math.radians(lat_deg)
            lon_rad = math.radians(lon_deg)
            v_n, v_e = heading_to_ned(spd_kt, crs_deg)

            gps_coor = GpsCoordinate(lat=lat_rad, lon=lon_rad, alt=0.0)
            gps_vel  = GpsVelocity(vN=v_n, vE=v_e, vD=0.0)
            if (ekf.initialized()):
                ekf.correct(gps_vel, gps_coor)
            else:
                ekf.initialize(gps_vel, gps_coor)
        
    return KinematicState(
        position = np.zeros(3, dtype=float),
        velocity = np.zeros(3, dtype=float),
        attitude = np.zeros(3, dtype=float),
        angular_velocity = np.zeros(3, dtype=float),
    )

if __name__ == "__main__":
    i2c, ag_sensor, m_sensor, ser, ekf, mukf = localize_setup()
    current_time = time.time()
    while True:
        #quat, current_time = localize(current_time, i2c, ag_sensor, m_sensor, ser, ekf, mukf)
        """
        e = Rotation.from_quat(quat).as_euler("ZYX", degrees=True)
        print(f"Latitude: {math.degrees(ekf.get_latitude_rad())}, "
              f"Longitude: {math.degrees(ekf.get_longitude_rad())}, "
              f"Pitch: {e[1]}, "
              f"Roll: {e[0]}, "
              f"Heading: {e[2]}")
        time.sleep(0.1)
        """
