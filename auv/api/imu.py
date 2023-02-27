# Custom imports
from Adafruit_BNO055.BNO055 import BNO055 as super_imu
import time
from datetime import datetime


class IMU(super_imu):
    """ Utilize inheritance of the low-level parent class """

    def __init__(self, serial_port, rst):
        """ Simply call our superclass constructor """
        super().__init__()
        sw, bl, accel, mag, gyro = super().get_revision()
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
        sys, gyro, accel, mag = super().get_calibration_status()
        x, y, z = super().read_accelerometer()
        lx, ly, lz = super().read_linear_acceleration()
       # q1, q2, q3, q4 = super().read_quarternion()
        with open("imu_data.txt","a") as f:
           f.write("Time \n")
           f.write(str(datetime.now()))
           f.write("\n")
           f.write('Heading \n')
           f.write(str(heading))
           f.write("\n")
           f.write('Roll\n')
           f.write(str(roll))
           f.write("\n")
           f.write('Pitch\n')
           f.write(str(pitch))
           f.write("\n")
           f.write('Acceleration\n')
           f.write(str(x) + ',' + str(y) + ',' + str(z))
           f.write("\n")
           f.write('Linear acceleration\n')
           f.write(str(lx) + ',' + str(ly) + ',' + str(lz))
           f.write("\n")
          # f.write('Quarternion\n')
          # f.write(str(q1) + ',' + str(q2) + ',' + str(q3) + ',' + str(q4))
           f.close()

        return heading, roll, pitch
