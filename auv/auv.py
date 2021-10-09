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

# Custom imports
from queue import Queue
from api import Radio
from api import IMU
from api import Crc32
from api import PressureSensor
from api import MotorController
from api import MotorQueue
from missions import *

# Constants for the AUV
RADIO_PATH = '/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0'
IMU_PATH = '/dev/serial0'
PING = 0xFFFFFF
SEND_SLEEP_DELAY = 1
RECEIVE_SLEEP_DELAY = 0.1
PING_SLEEP_DELAY = 3
CONNECTION_TIMEOUT = 6

# Encoding headers
POSITION_DATA = 0b000
HEADING_DATA = 0b001
MISC_DATA = 0b010
TEMP_DATA = 0b10011
DEPTH_DATA = 0b011

DEPTH_ENCODE = DEPTH_DATA << 21
HEADING_ENCODE = HEADING_DATA << 17
MISC_ENCODE = MISC_DATA << 21

MAX_TIME = 600
MAX_ITERATION_COUNT = MAX_TIME / SEND_SLEEP_DELAY / 7

# determines if connected to BS
connected = False
lock = threading.Lock()
radio_lock = threading.Lock()


def log(val):
    print("[AUV]\t" + val)


# Responsibilites:
#   - receive data/commands
#   - update connected global variable
class AUV_Receive(threading.Thread):
    """ Class for the AUV object. Acts as the main file for the AUV. """

    def __init__(self, queue):
        self.radio = None
        self.pressure_sensor = None
        self.imu = None
        self.mc = MotorController()
        self.time_since_last_ping = 0.0
        self.current_mission = None
        self.timer = 0
        self.motor_queue = queue
        threading.Thread.__init__(self)

    def run(self):
        """ Constructor for the AUV """

        # Get all non-default callable methods in this class
        self.methods = [m for m in dir(AUV_Receive) if not m.startswith('__')]

        try:
            self.pressure_sensor = PressureSensor()
            self.pressure_sensor.init()
            log("Pressure sensor has been found")
        except:
            log("Pressure sensor is not connected to the AUV.")

        try:
            self.imu = IMU(IMU_PATH)
            log("IMU has been found.")
        except:
            log("IMU is not connected to the AUV on IMU_PATH.")

        try:
            self.radio = Radio(RADIO_PATH)
            log("Radio device has been found.")
        except:
            log("Radio device is not connected to AUV on RADIO_PATH.")

        self.main_loop()

    # TODO delete
    def x(self, data):
        self.mc.update_motor_speeds(data)

    def test_motor(self, motor):
        """ Method to test all 4 motors on the AUV """

        if motor == "FORWARD":  # Used to be LEFT motor
            self.mc.test_forward()
        elif motor == "TURN":  # Used to be RIGHT MOTOR
            self.mc.test_turn()
        elif motor == "FRONT":
            self.mc.test_front()
        elif motor == "BACK":
            self.mc.test_back()
        elif motor == "ALL":
            self.mc.test_all()
        else:
            raise Exception('No implementation for motor name: ', motor)

    def main_loop(self):
        global connected
        """ Main connection loop for the AUV. """

        log("Starting main connection loop.")
        while True:
            time.sleep(RECEIVE_SLEEP_DELAY)

            # Always try to update connection status.
            if time.time() - self.time_since_last_ping > CONNECTION_TIMEOUT:
                lock.acquire()
                # Line read was EMPTY, but 'before' connection status was successful? Connection verification failed.
                if connected is True:
                    log("Lost connection to BS.")

                    # reset motor speed to 0 immediately and flush buffer
                    self.mc.update_motor_speeds([0, 0, 0, 0])  # TODO: resurface
                    log("DEBUG TODO speeds reset")

                    # enforce check in case radio is not found
                    if self.radio is not None:
                        self.radio.flush()

                    connected = False

                lock.release()

            if self.radio is None or self.radio.is_open() is False:
                try:  # Try to connect to our devices.
                    self.radio = Radio(RADIO_PATH)
                    log("Radio device has been found!")
                except:
                    pass
            else:
                try:
                    # Read seven bytes (3 byte message, 4 byte checksum)
                    line = self.radio.read(7)

                    # self.radio.flush()

                    while(line != b'' and len(line) == 7):
                        # print("Line read ", line)
                        intline = int.from_bytes(line, "big")
                        checksum = Crc32.confirm(intline)
                        if not checksum:
                            continue
                        intline = intline >> 32
                        if intline == 0xFFFFFF:  # We have a ping!
                            log("PING")
                            self.time_since_last_ping = time.time()
                            # print("ping if statement")
                            # print(line)
                            lock.acquire()
                            if connected is False:
                                log("Connection to BS verified.")
                                connected = True

                                # TODO test case: set motor speeds
                                data = [1, 2, 3, 4]
                                self.x(data)
                            lock.release()
                        else:
                            # Line was read, but it was not equal to a BS_PING

                            # Decode into a normal utd-8 encoded string and delete newline character
                            #message = line.decode('utf-8').replace("\n", "")
                            print("NON-PING LINE READ WAS", str(line))
                            message = intline
                            # message = int(message)
                            # 0000001XSY or 0000000X

                            # navigation command
                            if (message & 0x020000 > 0):
                                x = (message & 0x01F600) >> 9
                                sign = (message & 0x000100) >> 8
                                y = (message & 0x0000FF)

                                if (sign == 1):
                                    y = y * -1

                                log("Running motor command with (x, y): " + str(x) + "," + str(y))
                                self.motor_queue.put((x, y, 0))

                            # Xbox Navigation Command
                            # 0x[1110][0000] [XXXX][XXXX] [YYYY][YYYY]
                            elif (message & 0xE00000 == 0xE00000):
                                # xbox command
                                x = (message & 0x7F00) >> 8
                                xsign = (message & 0x8000) >> 15
                                y = message & 0x7F
                                ysign = (message & 0x80) >> 7
                                if xsign == 1:
                                    x = -x
                                if ysign == 1:
                                    y = -y
                                print("Xbox Command:", x, y)

                                self.motor_queue.put((x, y, 1))

                            # misison command
                            else:
                                # TODO
                                x = (message & 0x3)
                                log("Start Command Run with (x): " + str(x))
                                self.start_mission(x)

                        line = self.radio.read(7)

                    # end while
                    self.radio.flush()

                except Exception as e:
                    log("Error: " + str(e))
                    self.radio.close()
                    self.radio = None
                    log("Radio is disconnected from pi!")
                    continue

            if(self.current_mission is not None):
                print(self.timer)
                self.current_mission.loop()

                # TODO statements because max time received
                self.timer = self.timer + 1
                if self.timer > MAX_ITERATION_COUNT:
                    # kill mission, we exceeded time
                    self.abort_mission()

    def start_mission(self, mission):
        """ Method that uses the mission selected and begin that mission """
        if(mission == 0):  # Echo-location.
            try:  # Try to start mission
                self.current_mission = Mission1(
                    self, self.mc, self.pressure_sensor, self.imu)
                self.timer = 0
                log("Successfully started mission " + str(mission) + ".")
                # self.radio.write(str.encode("mission_started("+str(mission)+")\n"))
            except Exception as e:
                raise Exception("Mission " + str(mission) +
                                " failed to start. Error: " + str(e))
        # elif(mission == 2):
        #     self.current_mission = Mission2()
        # if self.current_mission is None:
        #     self.current_mission = Mission1()

    def d_data(self):
        # TODO Set sending data flag
        # self.sending_data = true
        pass

    def abort_mission(self):
        aborted_mission = self.current_mission
        self.current_mission = None
        aborted_mission.abort_loop()
        log("Successfully aborted the current mission.")
        # self.radio.write(str.encode("mission_failed()\n"))


# Responsibilites:
#   - send data
class AUV_Send_Data(threading.Thread):
    """ Class for the AUV object. Acts as the main file for the AUV. """

    def run(self):
        """ Constructor for the AUV """
        self.radio = None
        self.pressure_sensor = None
        self.imu = None
        self.mc = MotorController()
        self.time_since_last_ping = 0.0
        self.current_mission = None
        self.timer = 0

        # Get all non-default callable methods in this class
        self.methods = [m for m in dir(AUV_Send_Data) if not m.startswith('__')]

        try:
            self.pressure_sensor = PressureSensor()
            self.pressure_sensor.init()
            log("Pressure sensor has been found")
        except:
            log("Pressure sensor is not connected to the AUV.")

        self.imu = IMU.BNO055(serial_port='/dev/serial0', rst=18)
        log("IMU has been found.")

        try:
            self.radio = Radio(RADIO_PATH)
            log("Radio device has been found.")
        except:
            log("Radio device is not connected to AUV on RADIO_PATH.")

        self.main_loop()

    def main_loop(self):
        """ Main connection loop for the AUV. """
        global connected

        log("Starting main sending connection loop.")
        while True:
            time.sleep(SEND_SLEEP_DELAY)

            if self.radio is None or self.radio.is_open() is False:
                print("TEST radio not connected")
                try:  # Try to connect to our devices.
                    self.radio = Radio(RADIO_PATH)
                    log("Radio device has been found!")
                except:
                    pass

            else:
                try:
                    lock.acquire()
                    if connected is True:  # Send our AUV packet as well.
                        lock.release()
                        # TODO default values in case we could not read anything
                        heading = 0
                        temperature = 0
                        pressure = 0
                        # IMU
                        if self.imu is not None:
                            try:
                                heading, _, _ = self.imu.read_euler()
                                #print('HEADING=', heading)

                                temperature = self.imu.read_temp()
                                #print('TEMPERATURE=', temperature)

                            except:
                                # TODO print statement, something went wrong!
                                heading = 0
                                temperature = 0
                                #self.radio.write(str.encode("log(\"[AUV]\tAn error occurred while trying to read heading and temperature.\")\n"))
                            split_heading = math.modf(heading)
                            decimal_heading = int(round(split_heading[0], 2) * 100)
                            whole_heading = int(split_heading[1])
                            whole_heading = whole_heading << 7
                            heading_encode = (HEADING_ENCODE | whole_heading | decimal_heading)

                            radio_lock.acquire()
                            self.radio.write(heading_encode, 3)
                            radio_lock.release()
                        # Pressure
                        if self.pressure_sensor is not None:
                            self.pressure_sensor.read()
                            # defaults to mbars
                            pressure = self.pressure_sensor.pressure()
                            mbar_to_depth = (pressure-1013.25)/1000 * 10.2
                            if mbar_to_depth < 0:
                                mbar_to_depth = 0
                            for_depth = math.modf(mbar_to_depth)
                            # standard depth of 10.2
                            decimal = int(round(for_depth[0], 1) * 10)
                            whole = int(for_depth[1])
                            whole = whole << 4
                            depth_encode = (DEPTH_ENCODE | whole | decimal)

                            radio_lock.acquire()
                            self.radio.write(depth_encode, 3)
                            radio_lock.release()
                        # Temperature radio
                        whole_temperature = int(temperature)
                        sign = 0
                        if whole_temperature < 0:
                            sign = 1
                            whole_temperature *= -1
                        whole_temperature = whole_temperature << 5
                        sign = sign << 11
                        temperature_encode = (MISC_ENCODE | sign | whole_temperature)

                        radio_lock.acquire()
                        self.radio.write(temperature_encode, 3)
                        radio_lock.release()

                    else:
                        lock.release()

                except Exception as e:
                    raise Exception("Error occured : " + str(e))


# Responsibilites:
#   - send ping
class AUV_Send_Ping(threading.Thread):
    def run(self):
        """ Constructor for the AUV """
        self.radio = None

        try:
            self.radio = Radio(RADIO_PATH)
            log("Radio device has been found.")
        except:
            log("Radio device is not connected to AUV on RADIO_PATH.")

        self.main_loop()

    def main_loop(self):
        """ Main connection loop for the AUV. """
        global connected

        log("Starting main ping sending connection loop.")
        while True:
            time.sleep(PING_SLEEP_DELAY)

            if self.radio is None or self.radio.is_open() is False:
                print("TEST radio not connected")
                try:  # Try to connect to our devices.
                    self.radio = Radio(RADIO_PATH)
                    log("Radio device has been found!")
                except Exception as e:
                    log("Failed to connect to radio: " + str(e))

            else:
                try:
                    # Always send a connection verification packet
                    radio_lock.acquire()
                    self.radio.write(PING, 3)
                    radio_lock.release()

                except Exception as e:
                    raise Exception("Error occured : " + str(e))


def main():
    """ Main function that is run upon execution of auv.py """
    queue = Queue()
    auv_motor_thread = MotorQueue(queue)
    auv_r_thread = AUV_Receive(queue)
    auv_s_thread = AUV_Send_Data()
    auv_ping_thread = AUV_Send_Ping()

    auv_motor_thread.start()
    auv_r_thread.start()
    auv_s_thread.start()
    auv_ping_thread.start()


if __name__ == '__main__':  # If we are executing this file as main
    main()
