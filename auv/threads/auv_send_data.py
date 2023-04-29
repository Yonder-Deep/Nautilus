from queue import Queue
from static import global_vars
from static import constants
from missions import *
from api import MotorController
from api import PressureSensor
from api import IMU
from api import Radio
from api import GPS
import math
import os
import threading
import sys
import struct
sys.path.append('..')


def get_heading_encode(data):
    pass

# Responsibilites:
#   - send data


class AUV_Send_Data(threading.Thread):
    """ Class for the AUV object. Acts as the main file for the AUV. """

    def __init__(self, pressure_sensor, imu, mc, gps, gps_q):
        """ Constructor for the AUV """
        self.pressure_sensor = pressure_sensor
        self.imu = imu
        self.mc = mc
        self.gps = gps
        self.gps_q = gps_q
        self.gps_connected = True if gps is not None else False
        self.latitude = 0
        self.longitude = 0
        self.time_since_last_ping = 0.0
        self.current_mission = None
        self.timer = 0

        self._ev = threading.Event()

        threading.Thread.__init__(self)


    def run(self):
        """ Main connection loop for the AUV. """

        global_vars.log("Starting main sending connection loop.")
        while not self._ev.wait(timeout=constants.SEND_SLEEP_DELAY):
            # time.sleep(SEND_SLEEP_DELAY)

            if global_vars.radio is None or global_vars.radio.is_open() is False:
                global_vars.connect_to_radio()
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
                        # GPS
                        self.send_positioning()

                    else:
                        constants.LOCK.release()

                except Exception as e:
                    global_vars.radio.close()
                    print("send data exception")
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
        global_vars.radio.write(heading_encode)
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
        movement = global_vars.movement_status
        print("Movement:", movement)
        movement = movement << 3

        message_encode = (constants.MISC_ENCODE | sign | whole_temperature | movement)
        constants.RADIO_LOCK.acquire()
        global_vars.radio.write(message_encode)
        constants.RADIO_LOCK.release()

    def send_depth(self):
        depth = self.get_depth()
        print("Depth=", depth)
        if depth < 0:
            depth = 0
        for_depth = math.modf(depth)
        # standard depth of 10.2
        decimal = int(round(for_depth[0], 1) * 10)
        whole = int(for_depth[1])
        whole = whole << 4
        depth_encode = (constants.DEPTH_ENCODE | whole | decimal)

        constants.RADIO_LOCK.acquire()
        global_vars.radio.write(depth_encode)
        constants.RADIO_LOCK.release()

    def send_positioning(self):
        if (self.gps_connected):
            self.gps.run()
            gps_data = self.gps_q.get()
            if gps_data['has fix'] == 'Yes':
                self.latitude = gps_data['latitude']
                self.longitude = gps_data['longitude']
                self.latitude = round(self.latitude, 6)
                self.longitude = round(self.longitude, 6)

                lat, long = str(self.latitude), str(self.longitude)
                lat_whole, lat_dec = lat.split('.')
                long_whole, long_dec = long.split('.')
                lat_wi, long_wi = int(lat_whole), int(long_whole)
                lat_di, long_di = int(lat_dec), int(long_dec)

                if lat_wi < 0:
                    lat_s = 1
                    lat_wi *= -1
                else:
                    lat_s = 0

                if long_wi < 0:
                    long_s = 1
                    long_wi *= -1
                else:
                    long_s = 0

                '''
                print(str(x) + ", " + str(y))
                print(str(float.hex(x)) + ", " + str(float.hex(y)))
                print(xBytes)
                print(yBytes)
                '''

                lat_bits = (lat_s << 28) | (lat_wi << 20) | lat_di
                long_bits = (long_s << 28) | (long_wi << 20) | long_di

                position_encode = (constants.POSITION_ENCODE | (lat_bits << 29) | long_bits)
                constants.RADIO_LOCK.acquire()
                print(bin(position_encode))
                global_vars.radio.write(position_encode)
                constants.RADIO_LOCK.release()
                #self.out_q.put("set_gps_status(\"Recieving data\")")
                print(lat + "," + long)
                print("Sending GPS data")

            else:
                self.latitude = 0
                self.longitude = 0

                position_encode = (constants.POSITION_ENCODE | (1 << 58))
                constants.RADIO_LOCK.acquire()
                print(bin(position_encode))
                global_vars.radio.write(position_encode)
                constants.RADIO_LOCK.release()

                #self.out_q.put("set_gps_status(\"No fix\")")
                print("No fix")

        else:
            print("GPS Not Connected")

    def send_dive_log(self):
        constants.RADIO_LOCK.acquire()
        filepath = os.path.dirname(os.path.dirname(__file__)) + "logs/" + DIVE_LOG
        global_vars.radio.write(os.path.getsize(filepath))
        constants.RADIO_LOCK.release()
        dive_log = open(os.path.dirname(os.path.dirname(__file__)) + "logs/" + DIVE_LOG, "rb")
        file_bytes = dive_log.read(constants.FILE_SEND_PACKET_SIZE)
        while file_bytes:
            constants.RADIO_LOCK.acquire()
            print(file_bytes)
            global_vars.bs_response_sent = False
            global_vars.radio.write(file_bytes)
            global_vars.file_packets_sent += 1
            constants.RADIO_LOCK.release()
            while global_vars.file_packets_sent != global_vars.file_packets_received:
                if global_vars.bs_response_sent == True:
                    global_vars.bs_response_sent = False
                    constants.RADIO_LOCK.acquire()
                    global_vars.radio.write(file_bytes)
                    constants.RADIO_LOCK.release()
            file_bytes = dive_log.read(constants.FILE_SEND_PACKET_SIZE)

        global_vars.sending_dive_log = False
        global_vars.file_packets_sent = 0
        global_vars.file_packets_received = 0
        global_vars.bs_response_sent = False
        dive_log.close()

    def stop(self):
        self._ev.set()

    def get_depth(self):
        # TODO: default if read fails
        if self.pressure_sensor is not None:
            try:
                self.pressure_sensor.read()
            except Exception as e:
                print("Failed to read in pressure. Error:", e)
            pressure = self.pressure_sensor.pressure()
            # TODO: Check if this is accurate, mbars to m
            depth = (pressure-1013.25)/1000 * 10.2
            return depth - global_vars.depth_offset
        else:
            global_vars.log("No pressure sensor found.")
            return None
