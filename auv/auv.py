'''
This class acts as the main functionality file for
the Nautilus AUV. The "mind and brain" of the mission.
'''
# System imports
import os
import sys
import threading
import time
import math

# TODO - #35 GPS
# TEMP import gps

# Custom imports
from queue import Queue
from api import Radio
from api import IMU
from api import Crc32
from api import PressureSensor
from api import MotorController
from api import MotorQueue
from api import GPS
from missions import *
from api import Indicator
from api import RealSenseCamera

from static import global_vars

from threads.auv_send_data import AUV_Send_Data
from threads.auv_send_ping import AUV_Send_Ping
from threads.auv_receive import AUV_Receive
from threads.autonomous_nav import Autonomous_Nav

from static import constants
from static import global_vars


def threads_active(ts):
    for t in ts:
        if t.is_alive():
            return True
    return False


def stop_threads(ts):
    for t in ts:
        t.stop()


def start_threads(ts, queue, halt):
    gps_q = Queue()
    autonav_to_receive = Queue()
    receive_to_autonav = Queue()

    # Initialize hardware
    try:
        indicator_LED = Indicator()
        global_vars.log("Starting Up")
    except:
        global_vars.log("Indicator LED not detected")

    try:
        pressure_sensor = PressureSensor()
        pressure_sensor.init()
        global_vars.log("Pressure sensor has been found")
    except:
        pressure_sensor = None
        global_vars.log("Pressure sensor is not connected to the AUV.")

    try:
        gps = GPS(gps_q)
        print("Successfully connected to GPS socket service.")
    except:
        gps = None
        print("Warning: Could not connect to a GPS socket service.")

    try:
        depth_cam = RealSenseCamera()
        print("Depth cam has been found.")
    except:
        depth_cam = None
        print("Depth cam could not be found.")

    '''
    try:
        imu = IMU(serial_port=constants.IMU_PATH, rst=constants.IMU_RESET_PIN)
        global_vars.log("IMU has been found.")
    except Exception as e:
        print(e)
        imu = None
        global_vars.log("IMU is not connected to the AUV on IMU_PATH.")
    '''
    imu = None

    global_vars.connect_to_radio()

    mc = MotorController()

    auv_motor_thread = MotorQueue(queue, halt)
    auv_auto_thread = Autonomous_Nav(queue, halt, pressure_sensor, imu, mc, gps, gps_q, depth_cam, receive_to_autonav, autonav_to_receive)
    auv_r_thread = AUV_Receive(queue, halt, pressure_sensor, imu, mc, gps, gps_q, autonav_to_receive, receive_to_autonav, auv_auto_thread)

    ts = []

    auv_s_thread = AUV_Send_Data(pressure_sensor, imu, mc, gps, gps_q)
    auv_ping_thread = AUV_Send_Ping()

    ts.append(auv_motor_thread)
    ts.append(auv_auto_thread)
    ts.append(auv_r_thread)
    ts.append(auv_s_thread)
    ts.append(auv_ping_thread)

    auv_motor_thread.start()
    auv_r_thread.start()
    auv_s_thread.start()
    auv_ping_thread.start()

    # TODO - #35 GPS
    #gps_thread = GPS_Runner(None)
    # gps_thread.start()


if __name__ == '__main__':  # If we are executing this file as main
    queue = Queue()
    halt = [False]

    ts = []

    start_threads(ts, queue, halt)

    try:
        while threads_active(ts):
            if global_vars.stop_all_threads:
                global_vars.stop_all_threads = False
                stop_threads(ts)

            if global_vars.restart_threads:
                global_vars.restart_threads = False
                stop_threads(ts)

                # Reinitialize and restart all threads
                queue = Queue()
                halt = [False]
                ts = []

                start_threads(ts, queue, halt)

            time.sleep(1)
    except KeyboardInterrupt:
        # kill threads
        for t in ts:
            if t.is_alive():
                t.stop()

    print("waiting to stop")
    while threads_active(ts):
        time.sleep(0.1)
    print('done')
