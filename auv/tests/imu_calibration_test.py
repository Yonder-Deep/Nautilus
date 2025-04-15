import threading
from api import IMU

class IMU_Calibration_Test(threading.Thread):
    def __init__(self, imu: IMU):
        super().__init__()

        self.imu = imu
        # self.data = (0,) * 6
        self.stop_event = threading.Event()

    def run(self):
        while not self.stop_event.is_set():
            #heading, roll, pitch = self.imu.read_euler()
            #system, gyro, accel, mag = self.imu.get_calibration_status()

            #self.data = (heading, roll, pitch, system, gyro, accel, mag)
            break 

    def stop(self):
        self.stop_event.set()
