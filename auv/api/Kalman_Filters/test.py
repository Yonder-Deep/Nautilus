import serial
import pynmea2
import board
import time
import math
import numpy as np

from adafruit_lis3mdl import LIS3MDL
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX as LSM6DS
from scipy.spatial.transform import Rotation

from extended import EKF, ImuData, GpsCoordinate, GpsVelocity
from unscented_quaternion import MUKF

# --- magnetometer calibration constants ---
B = np.array([   -8.74,   66.45,   72.97])

Ainv = np.array([[ 20.99558,  0.69913, -0.02586],
             [  0.69913, 25.16196,  0.28862],
             [ -0.02586,  0.28862, 21.00722]]);

def parse_gprmc(sentence: str):
    """
    Return (lat_deg, lon_deg, speed_kt, course_deg) or None on no‐fix.
    """
    msg = pynmea2.parse(sentence)
    # status 'A' means valid
    if getattr(msg, "status", None) != 'A':
        return None
    return msg.latitude, msg.longitude, msg.spd_over_grnd, msg.true_course

def heading_to_ned(speed_kt: float, course_deg: float):
    """
    Convert speed (knots) & course (deg) to NED velocities (m/s).
    """
    speed_ms = speed_kt * 0.514444
    rad = math.radians(course_deg) if course_deg is not None else 0.0
    v_n = speed_ms * math.cos(rad)
    v_e = speed_ms * math.sin(rad)
    return v_n, v_e


def main():
    prev_time = time.time()

    # I²C sensors
    i2c       = board.I2C()
    ag_sensor = LSM6DS(i2c)
    m_sensor  = LIS3MDL(i2c)

    # GPS serial
    ser = serial.Serial("/dev/gps0", baudrate=9600, timeout=1)

    ekf = EKF()
    mukf = MUKF()

    hard_bias = np.array([0.0417014, 0.12463496, 19.66087], dtype=np.float32)
    ekf.accel_bias[:] = hard_bias
    ekf.abx, ekf.aby, ekf.abz = hard_bias.tolist()

    gps_record = time.time()
    accel_record = time.time()
    while True:
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
            s = line.decode('utf-8', errors='ignore').strip()
            parsed = parse_gprmc(s)
            if parsed:
                lat_deg, lon_deg, spd_kt, crs_deg = parsed
                # Convert to radians for the filter
                lat_rad = math.radians(lat_deg)
                lon_rad = math.radians(lon_deg)
                # Horizontal velocities in NED
                v_n, v_e = heading_to_ned(spd_kt, crs_deg)
                # Build your EKF inputs
                gps_coor = GpsCoordinate(lat=lat_rad, lon=lon_rad, alt=0.0)
                gps_vel  = GpsVelocity(vN=v_n, vE=v_e, vD=0.0)
                if (ekf.initialized()):
                    ekf.correct(gps_vel, gps_coor)
                else:
                    ekf.initialize(gps_vel, gps_coor)
                gps_record = cur_time
        prev_time = cur_time

        w,x,y,z = q
        e = Rotation.from_quat([x,y,z,w]).as_euler("ZYX", degrees=True)
        e[0] = (-e[0]) % 360.0
        print(f"Time: {cur_time}, "
              f"Latitude: {math.degrees(ekf.get_latitude_rad())}, "
              f"Longitude: {math.degrees(ekf.get_longitude_rad())}, "
              f"Pitch: {e[1]}, "
              f"Roll: {e[2]}, "
              f"Heading: {e[0]}")

        previous = [am[0], am[1], am[2]]

        time.sleep(0.1)

if __name__ == "__main__":
    main()