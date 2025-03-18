import time
import threading
import platform
from queue import Queue, Empty

from api import IMU
from api import PressureSensor
from api import MotorController
from api import Indicator
from api import MockController

import config
from core import websocket_thread, Navigation, Control

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

def main_log(logging_queue=Queue, base_queue=Queue):
    thing = 0
    while(logging_queue.qsize() > 0):
        try:
            thing += 1
            log_message = logging_queue.get_nowait()
            if log_message:
                print(log_message)
                base_queue.put(log_message)
        except Empty:
            return  

if __name__ == "__main__":
    # This event is set so that all the threads know to end
    stop_event = threading.Event()

    # Anything put into this queue will be printed
    # to stdout & forwarded to frontend
    logging_queue = Queue()

    # Used for thread cleanup
    threads = []

    queue_to_base = Queue()
    queue_to_auv = Queue()
    ws_shutdown_q = Queue()
    websocket_thread = threading.Thread(target=websocket_thread, args=[stop_event, logging_queue, config.SOCKET_IP, config.SOCKET_PORT, config.PING_INTERVAL, queue_to_base, queue_to_auv, True, ws_shutdown_q])
    threads.append(websocket_thread)
    websocket_thread.start()
    ws_shutdown = ws_shutdown_q.get(block=True) # Needed to shut down server

    motor_controller = MotorController()
    if platform.system() == "Darwin":
        motor_controller = MockController()

    queue_input_nav = Queue() # Input from user & state input to nav
    queue_input_control = Queue() # State input to nav
    queue_nav_to_control = Queue() # Setpoint input to nav
    navigation_thread = Navigation(
            input_state_q=queue_input_nav,
            desired_state_q=queue_nav_to_control,
            logging_q=logging_queue,
            stop_event=stop_event)
    control_thread = Control(
            input_state_q=queue_input_control,
            desired_state_q=queue_nav_to_control,
            logging_q=logging_queue,
            controller=motor_controller,
            stop_event=stop_event)

    print("Beginning main loop")
    try:
        while True:
            main_log(logging_queue, queue_to_base)

            try:
                message_from_base = queue_to_auv.get_nowait()
                # Based on commands, execute functions and/or subroutines
                if message_from_base:
                    print("Message from base: " + str(message_from_base))
                    command = message_from_base["command"]
                    if command == "pidConstants":
                        print("Setting PID Constants")
                    elif command == "motorTest":
                        print("Starting motor test")
                        # motor_test = threading.Thread(motor_test)
                        # motor_test.start()

                        # Override control & nav thread
                        # go directly to MC

                    elif command == "headingTest":
                        print("Starting heading test")
                        # TODO: Make heading test a function w/ args
                        # heading_test = Heading_Test()
                        # heading_test.start()

                        # Override nav thread
                        # go directly to control thread

                    elif command == "mission":
                        print("Beginning mission")
                        goal_coordinate = message_from_base["content"]
                        print("Goal: " + str(goal_coordinate))
                        if not navigation_thread.is_alive():
                            threads.append(navigation_thread)
                            navigation_thread.start()
                            threads.append(control_thread)
                            control_thread.start()
                        queue_input_nav.put(goal_coordinate)

            except Empty:
                pass

    except KeyboardInterrupt:
        stop_event.set()
        print("Joining threads")
        ws_shutdown()
        for thread in threads:
            if thread.is_alive():
                thread.join
        print("All threads joined, process exiting")