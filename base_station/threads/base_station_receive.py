import sys
import os

# System imports
import serial
import time
import threading
from queue import Queue

# Custom imports
from api import Crc32
from api import Radio
from api import GPS
from api import decode_command

from static import constants
from static import global_vars


class BaseStation_Receive(threading.Thread):
    def __init__(self, in_q=None, out_q=None):
        """ Initialize Serial Port and Class Variables
        debug: debugging flag """

        # Call super-class constructor
        # Instance variables
        self.radio = None
        self.gps = None
        self.in_q = in_q
        self.out_q = out_q
        self.gps_q = Queue()
        self.manual_mode = True
        self.time_since_last_ping = 0.0

        # Call super-class constructor
        threading.Thread.__init__(self)

        # Try to assign our radio object
        try:
            self.radio = Radio(constants.RADIO_PATH)
            self.log("Successfully found radio device on RADIO_PATH.")
        except:
            self.log(
                "Warning: Cannot find radio device. Ensure RADIO_PATH is correct.")

        # Try to connect our Xbox 360 controller.

# XXX ---------------------- XXX ---------------------------- XXX TESTING AREA

        # Try to assign our GPS object connection to GPSD
        try:
            self.gps = GPS(self.gps_q)
            self.log("Successfully connected to GPS socket service.")
        except:
            self.log("Warning: Could not connect to a GPS socket service.")

    def calibrate_controller(self):
        """ Instantiates a new Xbox Controller Instance """
        # Construct joystick and check that the driver/controller are working.
        self.joy = None
        self.main.log("Attempting to connect xbox controller")
        while self.joy is None:
            self.main.update()
            try:
                # self.joy = xbox.Joystick() TODO
                raise Exception()
            except Exception as e:
                continue
        self.main.log("Xbox controller is connected.")

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
                self.log("Failed to convert the AUV's gps coordinates to UTM.")
        # else:
        #    self.log("The AUV did not report its latitude and longitude.")

    def mission_failed(self):
        """ Mission return failure from AUV. """
        self.manual_mode = True
        self.out_q.put("set_vehicle(True)")
        self.log("Enforced switch to manual mode.")

        self.log("The current mission has failed.")

    def run(self):
        """ Main threaded loop for the base station. """
        # Begin our main loop for this thread.

        while True:
            print(self.radio.is_open())

            time.sleep(0.5)

            # Always try to update connection status
            if time.time() - self.time_since_last_ping > constants.CONNECTION_TIMEOUT:
                # We are NOT connected to AUV, but we previously ('before') were. Status has changed to failed.
                constants.lock.acquire()
                if global_vars.connected is True:
                    self.out_q.put("set_connection(False)")
                    self.log("Lost connection to AUV.")
                    global_vars.connected = False
                constants.lock.release()

            # This executes if we never had a radio object, or it got disconnected.
            if self.radio is None or not os.path.exists(constants.RADIO_PATH):
                # This executes if we HAD a radio object, but it got disconnected.
                if self.radio is not None and not os.path.exists(constants.RADIO_PATH):
                    self.log("Radio device has been disconnected.")
                    self.radio.close()

                # Try to assign us a new Radio object
                try:
                    self.radio = Radio(constants.RADIO_PATH)
                    self.log(
                        "Radio device has been found on RADIO_PATH.")
                except Exception as e:
                    print("Radio error: ", str(e))

            # If we have a Radio object device, but we aren't connected to the AUV
            else:
                # Try to read line from radio.
                try:

                    # Read 7 bytes
                    line = self.radio.read(7)

                    while(line != b'' and len(line) == 7):
                        print('read line')
                        intline = int.from_bytes(line, "big")

                        checksum = Crc32.confirm(intline)

                        if not checksum:
                            print('invalid line*************')
                            print(bin(intline >> 32))
                            self.radio.flush()
                            self.radio.close()
                            self.radio = Radio(constants.RADIO_PATH)

                            break

                        intline = intline >> 32
                        header = intline >> 21     # get first 3 bits
                        # PING case
                        if intline == constants.PING:
                            self.time_since_last_ping = time.time()
                            constants.lock.acquire()
                            if global_vars.connected is False:
                                self.log("Connection to AUV verified.")
                                self.out_q.put("set_connection(True)")
                                global_vars.connected = True
                            constants.lock.release()
                        # Data cases
                        else:
                            print("HEADER_STR", header)
                            decode_command(self, header, intline)

                        line = self.radio.read(7)

                    self.radio.flush()

                except Exception as e:
                    print(str(e))
                    self.radio.close()
                    self.radio = None
                    self.log("Radio device has been disconnected.")
                    continue

            time.sleep(constants.THREAD_SLEEP_DELAY)

    def log(self, message):
        """ Logs the message to the GUI console by putting the function into the output-queue. """
        self.out_q.put("log('" + message + "')")
