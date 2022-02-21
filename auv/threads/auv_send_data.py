from static import global_vars
from static import constants
from missions import *
from api import MotorController
from api import PressureSensor
from api import IMU
from api import Radio
import math
import threading
import sys
sys.path.append('..')


def get_heading_encode(data):
    pass

# Responsibilites:
#   - send data


class AUV_Send_Data(threading.Thread):
    """ Class for the AUV object. Acts as the main file for the AUV. """

    def __init__(self):
        """ Constructor for the AUV """
        self.radio = None
        self.pressure_sensor = None
        self.imu = None
        self.mc = MotorController()
        self.time_since_last_ping = 0.0
        self.current_mission = None
        self.timer = 0

        self._ev = threading.Event()

        threading.Thread.__init__(self)

    def _init_hardware(self):
        try:
            self.pressure_sensor = PressureSensor()
            self.pressure_sensor.init()
            global_vars.log("Pressure sensor has been found")
        except:
            global_vars.log("Pressure sensor is not connected to the AUV.")

        self.imu = IMU.BNO055(serial_port=constants.IMU_PATH, rst=18)
        global_vars.log("IMU has been found.")

        try:
            if not self.imu.begin():
                print("Failed to initialize IMU!")
        except Exception as e:
            print("Exception thrown when initializing IMU:", e)

        # TODO copied over from example code
        # if not self.imu.begin():
        #    raise RuntimeError('Failed to initialize BNO055! Is the sensor connected?')

        try:
            self.radio = Radio(constants.RADIO_PATH)
            global_vars.log("Radio device has been found.")
        except:
            global_vars.log("Radio device is not connected to AUV on RADIO_PATH.")

    def run(self):
        """ Main connection loop for the AUV. """

        self._init_hardware()

        global_vars.log("Starting main sending connection loop.")
        while not self._ev.wait(timeout=constants.SEND_SLEEP_DELAY):
            # time.sleep(SEND_SLEEP_DELAY)

            if self.radio is None or self.radio.is_open() is False:
                print("TEST radio not connected")
                try:  # Try to connect to our devices.
                    self.radio = Radio(constants.RADIO_PATH)
                    global_vars.log("Radio device has been found!")
                except:
                    pass

            else:
                try:
                    constants.LOCK.acquire()
                    if global_vars.connected is True:  # Send our AUV packet as well.
                        constants.LOCK.release()
                        # IMU
                        if self.imu is not None:
                            self.send_heading()
                            self.send_misc_data()
                        # Pressure
                        if self.pressure_sensor is not None:
                            self.send_depth()

                        # TODO: Positioning, currently placeholder
                        self.send_positioning()

                    else:
                        constants.LOCK.release()

                except Exception as e:
                    raise Exception("Error occured : " + str(e))

    def send_heading(self):
        try:
            heading, _, _ = self.imu.read_euler()
            print('HEADING=', heading)
        except:
            # TODO print statement, something went wrong!
            heading = 0

        split_heading = math.modf(heading)
        decimal_heading = int(round(split_heading[0], 2) * 100)
        whole_heading = int(split_heading[1])
        whole_heading = whole_heading << 7
        heading_encode = (constants.HEADING_ENCODE | whole_heading | decimal_heading)

        constants.RADIO_LOCK.acquire()
        self.radio.write(heading_encode, 3)
        constants.RADIO_LOCK.release()

    def send_misc_data(self):
        """ Encodes and sends miscellaneous data to the base station. Currently sends
            temperature and movement status data to the base station. """
        try:
            temperature = self.imu.read_temp()
            print('TEMPERATURE=', temperature)
        except:
            # TODO print statement, something went wrong!
            temperature = 0
        # Temperature radio
        whole_temperature = int(temperature)
        sign = 0
        if whole_temperature < 0:
            sign = 1
            whole_temperature *= -1
        whole_temperature = whole_temperature << 7
        sign = sign << 13

        # Movement status data
        movement = 0 if self.mc.is_stopped() else self.mc.motion_type
        movement = movement << 3

        message_encode = (constants.MISC_ENCODE | sign | whole_temperature | movement)
        constants.RADIO_LOCK.acquire()
        self.radio.write(message_encode, 3)
        constants.RADIO_LOCK.release()

    def send_depth(self):
        # TODO: default if read fails
        pressure = 0
        try:
            self.pressure_sensor.read()
        except Exception as e:
            print("Failed to read in pressure. Error:", e)

        # defaults to mbars
        pressure = self.pressure_sensor.pressure()
        print("Current pressure:", pressure)
        mbar_to_depth = (pressure-1013.25)/1000 * 10.2
        if mbar_to_depth < 0:
            mbar_to_depth = 0
        for_depth = math.modf(mbar_to_depth)
        # standard depth of 10.2
        decimal = int(round(for_depth[0], 1) * 10)
        whole = int(for_depth[1])
        whole = whole << 4
        depth_encode = (constants.DEPTH_ENCODE | whole | decimal)

        constants.RADIO_LOCK.acquire()
        self.radio.write(depth_encode, 3)
        constants.RADIO_LOCK.release()

    def send_positioning(self):
        # TODO: Actually get positioning, currently placeholder
        x, y = 0, 0
        x_bits = abs(x) & 0x1FF
        y_bits = abs(y) & 0x1FF

        x_sign = 0 if x >= 0 else 1
        y_sign = 0 if y >= 0 else 1

        x_bits = x_bits | (x_sign << 9)
        y_bits = y_bits | (y_sign << 9)
        position_encode = (constants.POSITION_ENCODE | x_bits << 10 | y_bits)
        constants.RADIO_LOCK.acquire()
        print(bin(position_encode))
        self.radio.write(position_encode, 3)
        constants.RADIO_LOCK.release()

    def stop(self):
        self._ev.set()
