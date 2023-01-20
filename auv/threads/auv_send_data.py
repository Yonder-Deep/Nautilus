from static import global_vars
from static import constants
from missions import *
from api import MotorController
from api import PressureSensor
from api import IMU
from api import Radio
import math
import os
import time
import threading
import sys
sys.path.append('..')


def get_heading_encode(data):
    pass

# Responsibilites:
#   - send data


class AUV_Send_Data(threading.Thread):
    """ Class for the AUV object. Acts as the main file for the AUV. """

    def __init__(self, pressure_sensor, imu, mc):
        """ Constructor for the AUV """
        self.pressure_sensor = pressure_sensor
        self.imu = imu
        self.mc = mc
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
                    if global_vars.connected is True and not global_vars.sending_data:  # Send our AUV packet as well.
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
                    elif global_vars.connected and global_vars.sending_data:
                        constants.LOCK.release()
                        print("SEND DIVE LOG")
                        self.send_dive_log()
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
        global_vars.radio.write(heading_encode, 3)
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
        global_vars.radio.write(message_encode, 3)
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
        global_vars.radio.write(depth_encode, 3)
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
        # print(bin(position_encode))
        global_vars.radio.write(position_encode, 3)
        constants.RADIO_LOCK.release()

    def send_dive_log(self):

        global_vars.radio.write(constants.DOWNLOAD_LOG_ENCODE, 3)
        filename = [f for f in os.listdir(constants.LOG_FOLDER_PATH) if os.path.isfile(os.path.join(constants.LOG_FOLDER_PATH, f))][0]
        filepath = constants.LOG_FOLDER_PATH + filename
        constants.LOCK.acquire()
        constants.RADIO_LOCK.acquire()
        global_vars.radio.write_data(os.path.getsize(filepath), constants.FILE_SEND_PACKET_SIZE)   # Send size of log file
        global_vars.radio.write_data(filename, constants.FILE_SEND_PACKET_SIZE)    # Send name of log file
        constants.LOCK.release()
        constants.RADIO_LOCK.release()
        # Start sending contents of file
        dive_log = open(filepath, "rb")
        file_bytes = dive_log.read(constants.FILE_SEND_PACKET_SIZE)
        while file_bytes:
            print(file_bytes)
            file_bytes = file_bytes.decode()
            global_vars.bs_response_sent = False
            constants.LOCK.acquire()
            constants.RADIO_LOCK.acquire()
            global_vars.radio.write_data(file_bytes, constants.FILE_SEND_PACKET_SIZE)
            constants.LOCK.release()
            constants.RADIO_LOCK.release()
            global_vars.file_packets_sent += 1
            # TODO Implement checker for every packet sent over to basestation
            # Ensure that base station is receiving every packet sent
            while global_vars.file_packets_sent != global_vars.file_packets_received:
                # print(f"files sent: {global_vars.file_packets_sent}, files received: {global_vars.file_packets_received}")

                if global_vars.bs_response_sent == True:
                    global_vars.bs_response_sent = False
                    constants.LOCK.acquire()
                    constants.RADIO_LOCK.acquire()
                    global_vars.radio.write_data(file_bytes, constants.FILE_SEND_PACKET_SIZE)
                    constants.LOCK.release()
                    constants.RADIO_LOCK.release()
            file_bytes = dive_log.read(constants.FILE_SEND_PACKET_SIZE)

        global_vars.sending_data = False
        global_vars.file_packets_sent = 0
        global_vars.file_packets_received = 0
        global_vars.bs_response_sent = False
        dive_log.close()

        print("SENDING DATA FINISHED")

    # Send Hydrophone Recording to Base Station
    # TODO fix/finish implementing after send_dive_log() is completely finished
    def send_audio_file(self):
        constants.RADIO_LOCK.acquire()
        global_vars.radio.write(constants.DOWNLOAD_LOG_ENCODE, 3)
        filename = [f for f in os.listdir(constants.AUDIO_FOLDER_PATH) if os.path.isfile(os.path.join(constants.AUDIO_FOLDER_PATH, f))][0]

        filename = "testtesttesttesttesttesttesttesttesttesttestte.wav"
        filepath = constants.AUDIO_FOLDER_PATH + filename

        global_vars.radio.write_data(os.path.getsize(filepath), constants.FILE_SEND_PACKET_SIZE)   # Send size of audio file
        global_vars.radio.write_data(filename, constants.FILE_SEND_PACKET_SIZE)    # Send name of audio file

        # Start sending contents of file
        audio_file = open(filepath, "rb")
        file_bytes = audio_file.read(constants.FILE_SEND_PACKET_SIZE)
        while file_bytes:
            time.sleep(0.1)
            print(file_bytes)
            file_bytes = int.from_bytes(file_bytes, "big")
            global_vars.bs_response_sent = False
            global_vars.radio.write_data(file_bytes, constants.FILE_SEND_PACKET_SIZE)
            global_vars.file_packets_sent += 1
            # TODO add packet checker
            # Ensure that base station is receiving every packet sent
            # while global_vars.file_packets_sent != global_vars.file_packets_received:
            #     print(f"files sent: {global_vars.file_packets_sent}, files received: {global_vars.file_packets_received}")
            #     if global_vars.bs_response_sent == True:
            #         global_vars.bs_response_sent = False
            #         global_vars.radio.write_data(file_bytes, constants.FILE_SEND_PACKET_SIZE)
            file_bytes = audio_file.read(constants.FILE_SEND_PACKET_SIZE)

        constants.RADIO_LOCK.release()
        global_vars.sending_data = False
        global_vars.file_packets_sent = 0
        global_vars.file_packets_received = 0
        global_vars.bs_response_sent = False
        audio_file.close()
        print("SENDING AUDIO DATA FINISHED")

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
