""" This class manages the serial connection between the
AUV and Base Station along with sending controller
commands. """

import sys
import os

# System imports
import serial
import time
import math
import argparse
import threading
from queue import Queue

# Custom imports
from api import Crc32
from api import Radio
from api import Joystick
from api import xbox
from api import NavController
from api import GPS
from api import decode_command
#from api import checksum
from gui import Main

# Constants
THREAD_SLEEP_DELAY = 0.1  # Since we are the slave to AUV, we must run faster.
PING_SLEEP_DELAY = 3
RADIO_PATH = '/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0'

PING = 0xFFFFFF

CONNECTION_TIMEOUT = 6

# AUV Constants (these are also in auv.py)
MAX_AUV_SPEED = 100
MAX_TURN_SPEED = 50


# Navigation Encoding
NAV_ENCODE = 0b000000100000000000000000           # | with XSY (forward, angle sign, angle)
XBOX_ENCODE = 0b111000000000000000000000          # | with XY (left/right, down/up xbox input)
MISSION_ENCODE = 0b000000000000000000000000       # | with X   (mission)

# determines if connected to BS
connected = False
lock = threading.Lock()
radio_lock = threading.Lock()


class BaseStation_Receive(threading.Thread):
    def __init__(self, in_q=None, out_q=None):
        """ Initialize Serial Port and Class Variables
        debug: debugging flag """

        # Call super-class constructor
        # Instance variables
        self.radio = None
        self.nav_controller = None
        self.gps = None
        self.in_q = in_q
        self.out_q = out_q
        self.gps_q = Queue()
        self.manual_mode = True
        self.time_since_last_ping = 0.0

        # Call super-class constructor
        threading.Thread.__init__(self)

        # Get all non-default callable methods in this class
        self.methods = [m for m in dir(BaseStation) if not m.startswith(
            '__') and not m.startswith('_')]

        # Try to assign our radio object
        try:
            self.radio = Radio(RADIO_PATH)
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
        """ Instantiates a new Xbox Controller Instance and NavigationController """
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

        # Instantiate New NavController With Joystick
        self.nav_controller = NavController(
            self.joy, self.button_cb, self.debug)

        self.main.log("Controller is connected.")

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

        global connected
        global lock

        while True:
            time.sleep(0.5)

            # Always try to update connection status
            if time.time() - self.time_since_last_ping > CONNECTION_TIMEOUT:
                # We are NOT connected to AUV, but we previously ('before') were. Status has changed to failed.
                lock.acquire()
                if connected is True:
                    self.out_q.put("set_connection(False)")
                    self.log("Lost connection to AUV.")
                    connected = False
                lock.release()

            # This executes if we never had a radio object, or it got disconnected.
            if self.radio is None or not os.path.exists(RADIO_PATH):
                # This executes if we HAD a radio object, but it got disconnected.
                if self.radio is not None and not os.path.exists(RADIO_PATH):
                    self.log("Radio device has been disconnected.")
                    self.radio.close()

                # Try to assign us a new Radio object
                try:
                    self.radio = Radio(RADIO_PATH)
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
                        # intline = int(line,2)
                        checksum = Crc32.confirm(intline)
                        if not checksum:
                            continue
                        intline = intline >> 32
                        header = intline >> 21     # get first 3 bits
                        # PING case
                        if intline == PING:
                            self.time_since_last_ping = time.time()
                            lock.acquire()
                            if connected is False:
                                self.log("Connection to AUV verified.")
                                self.out_q.put("set_connection(True)")
                                connected = True
                            lock.release()
                        # Data cases
                        else:
                            decode_command(self, header, intline)

                        line = self.radio.read(7)

                    self.radio.flush()

                except Exception as e:
                    print(str(e))
                    self.radio.close()
                    self.radio = None
                    self.log("Radio device has been disconnected.")
                    continue

            time.sleep(THREAD_SLEEP_DELAY)

    def log(self, message):
        """ Logs the message to the GUI console by putting the function into the output-queue. """
        self.out_q.put("log('" + message + "')")


class BaseStation_Send(threading.Thread):
    def __init__(self, in_q=None, out_q=None):
        """ Initialize Serial Port and Class Variables
        debug: debugging flag """

        # Instance variables
        self.radio = None
        self.joy = None
        self.nav_controller = None
        self.in_q = in_q
        self.out_q = out_q
        self.manual_mode = True
        self.time_since_last_ping = 0.0

        # Call super-class constructor
        threading.Thread.__init__(self)

        # Get all non-default callable methods in this class
        self.methods = [m for m in dir(BaseStation) if not m.startswith(
            '__') and not m.startswith('_')]

        # Try to assign our radio object
        try:
            self.radio = Radio(RADIO_PATH)
            self.log("Successfully found radio device on RADIO_PATH.")
        except:
            self.log(
                "Warning: Cannot find radio device. Ensure RADIO_PATH is correct.")

        # Try to connect our Xbox 360 controller.

# XXX ---------------------- XXX ---------------------------- XXX TESTING AREA
        try:
            print("case0-----------------")
            self.joy = xbox.Joystick()
            print("case1")

            self.log("Successfuly found Xbox 360 controller.")
            print("case2")
        except:
            self.log("Warning: Cannot find xbox controller")

        try:
            self.nav_controller = NavController(self.joy)
            print("case3")

            self.log("Successfully created a Navigation with Controller object.")
            print("case4")
        except:
            self.log("Warning: Cannot find nav controller")


# XXX ---------------------- XXX ---------------------------- XXX TESTING AREA

    def check_tasks(self):
        """ This checks all of the tasks (given from the GUI thread) in our in_q, and evaluates them. """

        while not self.in_q.empty():
            task = "self." + self.in_q.get()
            # Try to evaluate the task in the in_q.
            try:
                eval(task)
            except Exception as e:
                print("Failed to evaluate in_q task: ", task)
                print("\t Error received was: ", str(e))

    def test_motor(self, motor):
        """ Attempts to send the AUV a signal to test a given motor. """
        lock.acquire()
        if not connected:
            lock.release()
            self.log("Cannot test " + motor +
                     " motor(s) because there is no connection to the AUV.")
        else:
            lock.release()
            radio_lock.acquire()
            if (motor == 'Forward'):
                self.radio.write((NAV_ENCODE | (10 << 9) | (0 << 8) | (0)) & 0xFFFFFF)
            elif (motor == 'Left'):
                self.radio.write((NAV_ENCODE | (0 << 9) | (1 << 8) | 90) & 0xFFFFFF)
            elif (motor == 'Right'):
                self.radio.write((NAV_ENCODE | (0 << 9) | (0 << 8) | 90) & 0xFFFFFF)
            radio_lock.release()

            self.log('Sending encoded task: test_motor("' + motor + '")')

            # self.radio.write('test_motor("' + motor + '")')

    def abort_mission(self):
        """ Attempts to abort the mission for the AUV."""
        lock.acquire()
        if not connected:
            lock.release()
            self.log(
                "Cannot abort mission because there is no connection to the AUV.")
        else:
            lock.release()
            # self.radio.write("abort_mission()")
            self.log("Sending task: abort_mission()")
            self.manual_mode = True

    def start_mission(self, mission):
        """  Attempts to start a mission and send to AUV. """
        lock.acquire()
        if connected is False:
            lock.release()
            self.log("Cannot start mission " + str(mission) +
                     " because there is no connection to the AUV.")
        else:
            lock.release()
            radio_lock.acquire()
            self.radio.write(MISSION_ENCODE | mission)
            radio_lock.release()
            self.log('Sending task: start_mission(' + str(mission) + ')')

    def run(self):
        """ Main sending threaded loop for the base station. """
        global connected
        global lock

        xbox_input = False

        # Begin our main loop for this thread.
        while True:
            time.sleep(THREAD_SLEEP_DELAY)
            self.check_tasks()

            # Check if we have an Xbox controller
            if self.joy is None:
                try:
                    # print("Creating joystick. 5 seconds...")
                    # self.joy = Joystick() TODO remove
                    self.nav_controller = NavController(self.joy)
                    # print("Done creating.")
                except Exception as e:
                    print("Xbox creation error: ", str(e))
                    pass

            # elif not self.joy.connected():
            #    self.log("Xbox controller has been disconnected.")
            #    self.joy = None
            #    self.nav_controller = None

            # This executes if we never had a radio object, or it got disconnected.
            if self.radio is None or not os.path.exists(RADIO_PATH):
                # This executes if we HAD a radio object, but it got disconnected.
                if self.radio is not None and not os.path.exists(RADIO_PATH):
                    self.log("Radio device has been disconnected.")
                    self.radio.close()

                # Try to assign us a new Radio object
                try:
                    self.radio = Radio(RADIO_PATH)
                    self.log(
                        "Radio device has been found on RADIO_PATH.")
                except Exception as e:
                    print("Radio error: ", str(e))

            # If we have a Radio object device, but we aren't connected to the AUV
            else:
                # Try to write line to radio.
                try:
                    # This is where secured/synchronous code should go.
                    lock.acquire()
                    if connected and self.manual_mode:
                        lock.release()
                        if self.joy is not None and self.joy.A():  # and self.joy.connected() and self.nav_controller is not None:
                            xbox_input = True

                            try:
                                # self.nav_controller.handle()
                                #self.radio.write("x(" + str(self.nav_controller.get_data()) + ")")
                                print("[XBOX] X:", self.joy.leftX())
                                print("[XBOX] Y:", self.joy.leftY())
                                print("[XBOX] A\t")

                                x = round(self.joy.leftX()*100)
                                y = round(self.joy.leftY()*100)

                                xsign = 0
                                ysign = 0

                                if x < 0:
                                    xsign = 1
                                    x *= -1
                                if y < 0:
                                    ysign = 1
                                    y *= -1

                                xshift = x << 8
                                xsign = xsign << 15
                                ysign = ysign << 7
                                navmsg = XBOX_ENCODE | xsign | xshift | ysign | y

                                radio_lock.acquire()
                                self.radio.write(navmsg)
                                radio_lock.release()

                            except Exception as e:
                                self.log("Error with Xbox data: " + str(e))

                        # once A is no longer held, send one last zeroed out xbox command
                        if xbox_input and not self.joy.A():
                            radio_lock.acquire()
                            self.radio.write(XBOX_ENCODE)
                            radio_lock.release()
                            print("[XBOX] NO LONGER A\t")
                            xbox_input = False
                    else:
                        lock.release()
                except Exception as e:
                    print(str(e))
                    self.radio.close()
                    self.radio = None
                    self.log("Radio device has been disconnected.")
                    continue
            time.sleep(THREAD_SLEEP_DELAY)

    def log(self, message):
        """ Logs the message to the GUI console by putting the function into the output-queue. """
        self.out_q.put("log('" + message + "')")

    def close(self):
        """ Function that is executed upon the closure of the GUI (passed from input-queue). """
        os._exit(1)  # => Force-exit the process immediately.

# Responsibilites:
#   - send ping


class BaseStation_Send_Ping(threading.Thread):
    def run(self):
        """ Constructor for the AUV """
        self.radio = None

        try:
            self.radio = Radio(RADIO_PATH)
            print("Radio device has been found.")
        except:
            print("Radio device is not connected to AUV on RADIO_PATH.")

        self.main_loop()

    def main_loop(self):
        """ Main connection loop for the AUV. """
        global connected

        print("Starting main ping sending connection loop.")
        while True:
            time.sleep(PING_SLEEP_DELAY)

            if self.radio is None or self.radio.is_open() is False:
                print("TEST radio not connected")
                try:  # Try to connect to our devices.
                    self.radio = Radio(RADIO_PATH)
                    print("Radio device has been found!")
                except Exception as e:
                    print("Failed to connect to radio: " + str(e))

            else:
                try:
                    # Always send a connection verification packet
                    radio_lock.acquire()
                    self.radio.write(PING)
                    radio_lock.release()

                except Exception as e:
                    raise Exception("Error occured : " + str(e))


class BaseStation(threading.Thread):
    """ Base station class that acts as the brain for the entire base station. """

    def d(self, bytes):
        # TODO
        # Append new bytes to local data string/byte array
        # local_data += bytes
        pass

    def d_done(self):
        # TODO write data to file
        # write(local_data)
        # local_data.clear
        pass

    def download_data(self):
        """ Function calls download data function """
        lock.acquire()
        if connected is True:
            lock.release()
            # self.radio.write("d_data()")
            self.log("Sending download data command to AUV.")
        else:
            lock.release()
            self.log("Cannot download data because there is no connection to the AUV.")

    def mission_started(self, index):
        """ When AUV sends mission started, switch to mission mode """
        if index == 0:  # Echo location mission.
            self.manual_mode = False
            self.out_q.put("set_vehicle(False)")
            self.log("Switched to autonomous mode.")

        self.log("Successfully started mission " + str(index))


def main():
    """ Main method responsible for developing the main objects used during runtime
    like the BaseStation and Main objects. """

    # Define Queue data structures in order to communicate between threads.
    to_GUI = Queue()
    to_BS = Queue()

    # Create a BS (base station) and GUI object thread.
    try:
        bs_r_thread = BaseStation_Receive(to_BS, to_GUI)
        bs_s_thread = BaseStation_Send(to_BS, to_GUI)
        bs_ping_thread = BaseStation_Send_Ping()

        bs_r_thread.start()
        bs_s_thread.start()
        bs_ping_thread.start()
    except Exception as e:
        print("Err: ", str(e))
        print("[MAIN] Base Station initialization failed. Closing...")
        sys.exit()

    # Create main GUI object
    try:
        gui = Main(to_GUI, to_BS)
    except KeyboardInterrupt:
        print("CLOSING")
        quit()


if __name__ == '__main__':
    main()
