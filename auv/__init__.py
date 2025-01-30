import time
import threading
from queue import Queue, Empty

from api import IMU
from api import PressureSensor
from api import MotorController
from threads import GPS
from api import Indicator


from tests import IMU_Calibration_Test

from static import constants, global_vars

def threads_active(threads):
    for t in threads:
        if t.is_alive():
            return True
    return False


def stop_threads(threads):
    for t in threads:
        t.stop()


def start_threads(threads, queue, halt):
    gps_q = Queue()
    autonav_to_receive = Queue()
    receive_to_autonav = Queue()

    # Initialize hardware
    try:
        indicator_LED = Indicator()
        print("Starting Up")
    except:
        print("Indicator LED not detected")

    try:
        pressure_sensor = PressureSensor()
        pressure_sensor.init()
        print("Pressure sensor has been found")
    except:
        pressure_sensor = None
        print("Pressure sensor is not connected to the AUV.")

    try:
        gps = GPS(gps_q)
        print("Successfully connected to GPS socket service.")
    except Exception as error:
        gps = None
        print("GPS not found")
        print(error)

    try:
        depth_cam = RealSenseCamera()
        print("Depth cam has been found.")
    except:
        depth_cam = None
        print("Depth cam could not be found.")

    try:
        imu = IMU()
        print("IMU has been found.")
    except Exception as e:
        print(e)
        imu = None
        print("IMU is not connected to the AUV on IMU_PATH.")

    mc = MotorController()

    # auv_auto_thread = Autonomous_Nav(queue, halt, pressure_sensor, imu, mc, gps, gps_q, depth_cam, receive_to_autonav, autonav_to_receive)
    auv_auto_thread = None

    imu_calibration_test = IMU_Calibration_Test(imu)

    threads = []

    threads.append(auv_auto_thread)
    threads.append(imu_calibration_test)

    imu_calibration_test.start()
    if gps is not None:
        gps.start()


if __name__ == "__main__":  # If we are executing this file as main
    queue_to_base = Queue()
    queue_to_auv = Queue()

    websocket_thread = threading.Thread(target="websocket_handler", args=[constants.BASE_IP_ADDRESS, constants.PING_INTERVAL, queue_to_base, queue_to_auv])

    try:
        while True:
            time.sleep(0.01)
            try:
                queue_to_auv.get(block=False)
            # Based on commands, execute functions and/or subroutines
            except Empty:
                pass
    except KeyboardInterrupt:
        websocket_thread.join()

    print("Waiting for threads to stop")
    while threads_active(threads):
        time.sleep(0.1)
    print("Shutdown done")
