from glob import glob
import sys
import os
import bz2

# System imports
import serial
import time
import threading
import utm
from queue import Queue

# Custom imports
from api import Crc32
from api import Radio
from api import GPS
from api import decode_command
from api import xbox
from static import constants
from static import global_vars


class BaseStation_Receive(threading.Thread):
    def __init__(self, radio, in_q=None, out_q=None):
        """ Initialize Serial Port and Class Variables
        debug: debugging flag """

        # Call super-class constructor
        # Instance variables
        self.gps = None
        self.in_q = in_q
        self.out_q = out_q
        self.gps_q = Queue()
        self.manual_mode = True
        self.time_since_last_ping = 0.0

        # Call super-class constructor
        threading.Thread.__init__(self)

        # Try to assign our radio object
        self.radio = radio

        try:
            self.gps = GPS(self.gps_q)
            global_vars.log(self.out_q, "Successfully connected to GPS socket service.")
        except:
            global_vars.log(self.out_q, "Warning: Could not connect to a GPS socket service.")

    def calibrate_controller(self):
        """ Instantiates a new Xbox Controller Instance """
        # Construct joystick and check that the driver/controller are working.
        self.joy = None
        global_vars.log(self.out_q, "Attempting to connect xbox controller")
        while self.joy is None:
            try:
                self.joy = xbox.Joystick()

            except Exception as e:
                print("Joystick exception: ", e)
                continue

        global_vars.log(self.out_q, "Xbox controller is connected.")

    def auv_data(self, heading, temperature, pressure, movement, mission, flooded, control, longitude=None, latitude=None):
        """ Parses the AUV data-update packet, stores knowledge of its on-board sensors"""

        # Update movement status on BS and on GUI
        self.auv_movement = movement
        self.out_q.put("set_movement("+str(movement)+")")

        # Update mission status on BS and on GUI
        self.auv_mission = mission
        self.out_q.put("set_mission_status("+str(mission)+")")

        # Update flooded status on BS and on GUI
        self.auv_flooded = flooded
        self.out_q.put("set_flooded("+str(flooded)+")")

        # Update control status on BS and on GUI
        self.auv_control = control
        self.out_q.put("set_control("+str(control)+")")

        # Update heading on BS and on GUI
        self.auv_heading = heading
        self.out_q.put("set_heading("+str(heading)+")")

        # Update temp on BS and on GUI
        self.auv_temperature = temperature
        self.out_q.put("set_temperature("+str(temperature)+")")

        # Update pressure on BS and on GUI
        self.auv_pressure = pressure
        self.out_q.put("set_pressure(" + str(pressure) + ")")

        # Update depth on BS and on GUI
        self.depth = pressure / 100  # 1 mBar = 0.01 msw
        self.out_q.put("set_depth(" + str(self.depth) + ")")

        # If the AUV provided its location...
        if longitude is not None and latitude is not None:
            self.auv_longitude = longitude
            self.auv_latitude = latitude
            try:    # Try to convert AUVs latitude + longitude to UTM coordinates, then update on the GUI thread.
                self.auv_utm_coordinates = utm.from_latlon(longitude, latitude)
                self.out_q.put("add_auv_coordinates(" + self.auv_utm_coordinates[0] + ", " + self.auv_utm_coordinates[1] + ")")
            except:
                global_vars.log(self.out_q, "Failed to convert the AUV's gps coordinates to UTM.")
        else:
            global_vars.log(self.out_q, "The AUV did not report its latitude and longitude.")

    def mission_failed(self):
        """ Mission return failure from AUV. """
        self.manual_mode = True
        self.out_q.put("set_vehicle(True)")
        global_vars.log(self.out_q, "Enforced switch to manual mode.")

        global_vars.log(self.out_q, "The current mission has failed.")

    def decompress(self,file_path,file_decomp_path): # TODO: Test 
        f = open(file_path,"rb")
        f_decomp = open(file_decomp_path,"wb")
        input = f.read()
        decomp_output = bz2.decompress(input)
        f_decomp.write(decomp_output)
        return decomp_output

    def run(self):
        """ Main threaded loop for the base station. """
        # Begin our main loop for this thread.

        while True:
            time.sleep(0.5)

            # Always try to update connection status
            if time.time() - self.time_since_last_ping > constants.CONNECTION_TIMEOUT:
                # We are NOT connected to AUV, but we previously ('before') were. Status has changed to failed.
                constants.lock.acquire()
                if global_vars.connected is True:
                    self.out_q.put("set_connection(False)")
                    global_vars.log(self.out_q, "Lost connection to AUV.")
                    global_vars.connected = False
                constants.lock.release()

            # This executes if we never had a radio object, or it got disconnected.
            if self.radio is None or not global_vars.path_existance(constants.RADIO_PATHS):
                # This executes if we HAD a radio object, but it got disconnected.
                if self.radio is not None and not global_vars.path_existance(constants.RADIO_PATHS):
                    global_vars.log(self.out_q, "Radio device has been disconnected.")
                    self.radio.close()

                # Try to assign us a new Radio object
                global_vars.connect_to_radio(self.out_q)
                self.radio = global_vars.radio

            # If we have a Radio object device, but we aren't connected to the AUV
            else:
                # Try to read line from radio.
                try:

                    # Read 7 bytes
                    line = self.radio.read(7)

                    while (line != b'' or global_vars.downloading_file):
                        if not global_vars.downloading_file and len(line) == 7:
                            print('read line')
                            intline = int.from_bytes(line, "big")
                            print(f"THIS IS INTLINE: {intline}")
                            checksum = Crc32.confirm(intline)

                            if not checksum:
                                print('invalid line*************')
                                print(bin(intline >> 32))
                                self.radio.flush()
                                self.radio.close()
                                self.radio, output_msg = global_vars.connect_to_radio(self.out_q)
                                global_vars.log(self.out_q, output_msg)
                                break

                            intline = intline >> 32
                            header = intline >> 21     # get first 3 bits
                            # PING case
                            if intline == constants.PING:  # TODO MIGHT NEED TO CHANGE
                                self.time_since_last_ping = time.time()
                                print("[BS] Received ping")
                                constants.lock.acquire()
                                if global_vars.connected is False:
                                    global_vars.log(self.out_q, "Connection to AUV verified.")
                                    self.out_q.put("set_connection(True)")
                                    global_vars.connected = True
                                constants.lock.release()
                            # Data cases
                            else:
                                print("HEADER_STR", header)
                                decode_command(self, header, intline)
                            # Check if an entire file is being sent from AUV
                            if header == constants.FILE_DATA:
                                print("[BS] THIS IF BLOCK RAN ------------------")
                                intline = int.from_bytes(line, "big")
                                isAudio = True if 0b1 & intline == 0b1 else False
                                file = None
                                global_vars.downloading_file = True
                                continue
                            line = self.radio.read(7)
                        elif global_vars.downloading_file:
                            # Handles receiving an entire file from the AUV
                            line = b''
                            while line == b'':
                                line = self.radio.read(constants.FILE_DL_PACKET_SIZE)

                            intline = int.from_bytes(line, "big")
                            print(f"intline: {intline}")

                            # Get first packet containing final file size
                            if global_vars.file_size == 0:
                                global_vars.file_size = intline
                                continue
                            # Get second packet containing file name (includes file format)
                            if file is None:
                                downloaded_filename = line.decode("utf-8")

                                if isAudio:
                                    file = open(constants.AUDIO_FOLDER_PATH + downloaded_filename, "wb")
                                else:
                                    file = open(constants.LOG_FOLDER_PATH + downloaded_filename, "wb")
                                continue
                            # Get packets of file contents, keep track of number of packets received
                            global_vars.file_packets_received += 1
                            global_vars.packet_received = True
                            print(f"files received: {global_vars.file_packets_received}")
                            print(f"line: {line}")
                            # Write to file
                            file.write(line)
                            # Get current file size
                            file.seek(0, os.SEEK_END)
                            curr_file_size = file.tell()
                            # Return to normal operations when correct file size reached
                            print(curr_file_size, global_vars.file_size)
                            if curr_file_size >= global_vars.file_size:
                                print("[BS] CLOSING THE LOG FILE")
                                file.close()
                                global_vars.downloading_file = False
                                global_vars.file_size = 0
                                global_vars.packet_received = False
                                global_vars.file_packets_received = 0
                                line = self.radio.read(7)

                    self.radio.flush()

                except Exception as e:
                    print(str(e))
                    self.radio.close()
                    self.radio = None
                    global_vars.log(self.out_q, "Radio device has been disconnected.")
                    continue

            time.sleep(constants.THREAD_SLEEP_DELAY)
