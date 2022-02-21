import os

# System imports
import serial
import time
import threading
from queue import Queue

# Custom imports
from api import Radio
from api import xbox

from static import constants
from static import global_vars

# Navigation Encoding
NAV_ENCODE = 0b000000100000000000000000           # | with XSY (forward, angle sign, angle)
XBOX_ENCODE = 0b111000000000000000000000          # | with XY (left/right, down/up xbox input)
MISSION_ENCODE = 0b000000000000000000000000       # | with X   (mission)
DIVE_ENCODE = 0b110000000000000000000000           # | with D   (depth)
KILL_ENCODE = 0b001000000000000000000000          # | with X (kill all / restart threads)

# Action Encodings
HALT = 0b010
CAL_DEPTH = 0b011
ABORT = 0b100
DL_DATA = 0b101


class BaseStation_Send(threading.Thread):
    def __init__(self, in_q=None, out_q=None):
        """ Initialize Serial Port and Class Variables
        debug: debugging flag """

        # Instance variables
        self.radio = None
        self.joy = None
        self.in_q = in_q
        self.out_q = out_q
        self.manual_mode = True

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
        try:
            print("case0-----------------")
            self.joy = xbox.Joystick()
            print("case1")

            self.log("Successfuly found Xbox 360 controller.")
            print("case2")
        except:
            self.log("Warning: Cannot find xbox controller")


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
        constants.lock.acquire()
        if not global_vars.connected:
            constants.lock.release()
            self.log("Cannot test " + motor +
                     " motor(s) because there is no connection to the AUV.")
        else:
            constants.lock.release()
            constants.radio_lock.acquire()
            if (motor == 'Forward'):
                self.radio.write((NAV_ENCODE | (10 << 9) | (0 << 8) | (0)) & 0xFFFFFF)
            elif (motor == 'Left'):
                self.radio.write((NAV_ENCODE | (0 << 9) | (1 << 8) | 90) & 0xFFFFFF)
            elif (motor == 'Right'):
                self.radio.write((NAV_ENCODE | (0 << 9) | (0 << 8) | 90) & 0xFFFFFF)
            constants.radio_lock.release()

            self.log('Sending encoded task: test_motor("' + motor + '")')

            # self.radio.write('test_motor("' + motor + '")')

    def abort_mission(self):
        """ Attempts to abort the mission for the AUV."""
        constants.lock.acquire()
        if not global_vars.connected:
            constants.lock.release()
            self.log(
                "Cannot abort mission because there is no connection to the AUV.")
        else:
            constants.lock.release()
            # self.radio.write("abort_mission()")
            self.log("Sending task: abort_mission()")
            self.manual_mode = True

    def start_mission(self, mission, depth, t):
        """  Attempts to start a mission and send to AUV. """
        constants.lock.acquire()
        if global_vars.connected is False:
            constants.lock.release()
            self.log("Cannot start mission " + str(mission) +
                     " because there is no connection to the AUV.")
        else:
            constants.lock.release()
            depth = (depth << 12) & 0x3F000
            t = (t << 3) & 0xFF8
            constants.radio_lock.acquire()
            self.radio.write(MISSION_ENCODE | depth | t | mission)
            print(bin(MISSION_ENCODE | depth | t | mission))

            constants.radio_lock.release()
            self.log('Sending task: start_mission(' + str(mission) + ')')

    def send_halt(self):
        self.start_mission(HALT, 0, 0)

    def send_calibrate_depth(self):
        self.start_mission(CAL_DEPTH, 0, 0)

    def send_abort(self):
        self.start_mission(ABORT, 0, 0)

    def send_download_data(self):
        self.start_mission(DL_DATA, 0, 0)

    def send_dive(self, depth):
        constants.lock.acquire()
        if global_vars.connected is False:
            constants.lock.release()
            self.log("Cannot dive because there is no connection to the AUV.")
        else:
            constants.lock.release()
            constants.radio_lock.acquire()
            self.radio.write(DIVE_ENCODE | depth)
            print(bin(DIVE_ENCODE | depth))
            constants.radio_lock.release()
            self.log('Sending task: dive(' + str(depth) + ')')  # TODO: change to whatever the actual command is called

    def encode_xbox(self, x, y, right_trigger):
        """ Encodes a navigation command given xbox input. """
        xsign, ysign, vertical = 0, 0, 0

        if x < 0:
            xsign = 1
            x *= -1
        if y < 0:
            ysign = 1
            y *= -1
        if right_trigger:
            vertical = 1

        xshift = x << 8
        xsign = xsign << 15
        ysign = ysign << 7
        vertical = vertical << 16
        return XBOX_ENCODE | vertical | xsign | xshift | ysign | y

    def run(self):
        """ Main sending threaded loop for the base station. """
        xbox_input = False

        # Begin our main loop for this thread.
        while True:
            time.sleep(constants.THREAD_SLEEP_DELAY)
            self.check_tasks()

            # Check if we have an Xbox controller
            if self.joy is None:
                try:
                    # print("Creating joystick. 5 seconds...")
                    # self.joy = Joystick() TODO remove
                    # print("Done creating.")
                    pass
                except Exception as e:
                    print("Xbox creation error: ", str(e))
                    pass

            # elif not self.joy.connected():
            #    self.log("Xbox controller has been disconnected.")
            #    self.joy = None

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
                # Try to write line to radio.
                try:
                    # This is where secured/synchronous code should go.
                    constants.lock.acquire()
                    if global_vars.connected and self.manual_mode:
                        constants.lock.release()
                        if self.joy is not None and self.joy.leftBumper() and self.joy.rightBumper():
                            # Read in potential kill-all/restart command
                            if self.joy.Guide():
                                # Send restart command
                                constants.radio_lock.acquire()
                                self.radio.write(KILL_ENCODE | 1)
                                constants.radio_lock.release()
                                print("Restarting AUV threads...")

                            elif self.joy.Back() and self.joy.Start():
                                # Send kill-all command
                                constants.radio_lock.acquire()
                                self.radio.write(KILL_ENCODE)
                                constants.radio_lock.release()
                                print("Killing AUV threads...")

                        if self.joy is not None and self.joy.A():
                            xbox_input = True

                            try:
                                print("[XBOX] X:", self.joy.leftX())
                                print("[XBOX] Y:", self.joy.leftY())
                                print("[XBOX] A\t")
                                print("[XBOX] Right Trigger:", self.joy.rightTrigger())

                                x = round(self.joy.leftX()*100)
                                y = round(self.joy.leftY()*100)
                                right_trigger = round(self.joy.rightTrigger()*10)

                                self.out_q.put("set_xbox_status(1," + str(right_trigger/10) + ")")
                                print(right_trigger)
                                navmsg = self.encode_xbox(x, y, right_trigger)

                                constants.radio_lock.acquire()
                                self.radio.write(navmsg)
                                constants.radio_lock.release()

                            except Exception as e:
                                self.log("Error with Xbox data: " + str(e))

                        # once A is no longer held, send one last zeroed out xbox command
                        if xbox_input and not self.joy.A():
                            constants.radio_lock.acquire()
                            self.radio.write(XBOX_ENCODE)
                            constants.radio_lock.release()
                            print("[XBOX] NO LONGER A\t")
                            self.out_q.put("set_xbox_status(0,0)")
                            xbox_input = False
                    else:
                        constants.lock.release()
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

    def close(self):
        """ Function that is executed upon the closure of the GUI (passed from input-queue). """
        # close the xbox controller
        if(self.joy is not None):
            self.joy.close()
        os._exit(1)  # => Force-exit the process immediately.

    def mission_started(self, index):
        """ When AUV sends mission started, switch to mission mode """
        if index == 0:  # Echo location mission.
            self.manual_mode = False
            self.out_q.put("set_vehicle(False)")
            self.log("Switched to autonomous mode.")

        self.log("Successfully started mission " + str(index))

# Responsibilites:
#   - send ping
