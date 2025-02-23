"""
magnetometer_calibration.py

This module provides functionality to calibrate a magnetometer by recording 
magnetic field strength in the x, y, and z directions. 

Calibration Process:
- The IMU should be moved in a figure-eight pattern to ensure exposure to 
  all orientations.
  
Output:
- mag_raw.csv: Contains raw magnetometer readings collected during calibration.
"""

from adafruit_lsm6ds.lsm6dsox import LSM6DSOX
import threading
import time
import csv
import board
import busio
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX
from adafruit_lis3mdl import LIS3MDL

class KeyListener:
    """Object for listening for input in a separate thread"""

    def __init__(self):
        self._input_key = None
        self._listener_thread = None

    def _key_listener(self):
        while True:
            self._input_key = input()

    def start(self):
        """Start Listening"""
        if self._listener_thread is None:
            self._listener_thread = threading.Thread(
                target=self._key_listener, daemon=True
            )
        if not self._listener_thread.is_alive():
            self._listener_thread.start()

    def stop(self):
        """Stop Listening"""
        if self._listener_thread is not None and self._listener_thread.is_alive():
            self._listener_thread.join()

    @property
    def pressed(self):
        "Return whether enter was pressed since last checked" ""
        result = False
        if self._input_key is not None:
            self._input_key = None
            result = True
        return result


def main():
    CALIBRATION_TIME = 60

    i2c = busio.I2C(board.SCL, board.SDA)
    magnetometer = LIS3MDL(i2c)
    key_listener = KeyListener()
    key_listener.start()

    ############################
    # Magnetometer Calibration #
    ############################

    print("Magnetometer Calibration")
    print("Press ENTER to start calibration")

    while not key_listener.pressed:
        pass

    print("Start moving the board in all directions for {} seconds".format(CALIBRATION_TIME))

    data = []
    start_time = time.time()

    while not key_listener.pressed and (time.time() - start_time) < CALIBRATION_TIME:
        mag_x, mag_y, mag_z = magnetometer.magnetic
        data.append([mag_x, mag_y, mag_z])
        print(
            "Magnetometer: X: {0:8.2f}, Y:{1:8.2f}, Z:{2:8.2f} uT".format(
                mag_x, mag_y, mag_z
            )
        )
        print("")
        time.sleep(0.1)

    if key_listener.pressed:
        print("Calibration stopped due to keyboard input.")
    elif (time.time() - start_time) >= CALIBRATION_TIME:
        with open('mag_raw.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        print("Calibration completed successfully")

if __name__ == "__main__":
    main()
