import time
import threading
from queue import Queue, Empty

from api import IMU
from api import PressureSensor
from api import MotorController
from api import Indicator

from threads import websocket_thread
from static import constants, global_vars
from tests import IMU_Calibration_Test, Heading_Test, motor_test

def start_threads(threads, queue, halt):
    gps_q = Queue()

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

    motor_controller = MotorController()

    # auv_auto_thread = Autonomous_Nav(queue, halt, pressure_sensor, imu, mc, gps, gps_q, depth_cam, receive_to_autonav, autonav_to_receive)
    auv_auto_thread = None

    imu_calibration_test = IMU_Calibration_Test(imu)

    imu_calibration_test.start()
    if gps is not None:
        gps.start()


if __name__ == "__main__":
    queue_to_base = Queue()
    queue_to_auv = Queue()
    logging_queue = Queue()

    stop_event = threading.Event()

    indicator = Indicator()
    motor_controller = MotorController()
    imu = IMU
    imu_calibration_test = IMU_Calibration_Test(imu)

    websocket_thread = threading.Thread(target=websocket_thread, args=[stop_event, logging_queue, constants.SOCKET_IP, constants.SOCKET_PORT, constants.PING_INTERVAL, queue_to_base, queue_to_auv, True])
    websocket_thread.start()

    print("Beginning main loop")
    try:
        while True:
            time.sleep(0.01)

            try:
                log_message = logging_queue.get_nowait()
                if log_message:
                    print(log_message)
            except Empty:
                pass

            try:
                message_from_base = queue_to_auv.get_nowait()
                # Based on commands, execute functions and/or subroutines
                if message_from_base :
                    print("Message from base: " + str(message_from_base))
                    command = message_from_base["command"]
                    if command == "pidConstants":
                        print("Setting PID Constants")
                    elif command == "motorTest":
                        print("Starting motor test")
                        motor_test = threading.Thread(motor_test)
                        motor_test.start()
                    elif command == "headingTest":
                        print("Starting heading test")
                        # TODO: Make heading test a function w/ args
                        heading_test = Heading_Test()
                        heading_test.start()

            except Empty:
                pass

    except KeyboardInterrupt:
        stop_event.set()
        print("Joining threads")
        websocket_thread.join()
        print("All threads joined, process exiting")