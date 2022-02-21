from missions import *
from api import MotorQueue
from api import MotorController
from api import PressureSensor
from api import Crc32
from api import IMU
from api import Radio
from queue import Queue
from static import global_vars
from static import constants
import math
import time
import threading
import sys
sys.path.append('..')

# System imports

# Custom imports

# Responsibilites:
#   - receive data/commands
#   - update connected global variable


class AUV_Receive(threading.Thread):
    """ Class for the AUV object. Acts as the main file for the AUV. """

    def __init__(self, queue, halt, radio, pressure_sensor, imu, mc):
        self.radio = radio
        self.pressure_sensor = pressure_sensor
        self.imu = imu
        self.mc = mc
        self.time_since_last_ping = time.time() + 4
        self.current_mission = None
        self.timer = 0
        self.motor_queue = queue
        self.halt = halt               # List for MotorQueue to check updated halt status
        # Get all non-default callable methods in this class
        self.methods = [m for m in dir(AUV_Receive) if not m.startswith('__')]

        self._ev = threading.Event()
        threading.Thread.__init__(self)

    def run(self):
        """ Constructor for the AUV """

        # Get all non-default callable methods in this class
        self.methods = [m for m in dir(AUV_Receive) if not m.startswith('__')]

        self._ev = threading.Event()

        threading.Thread.__init__(self)

    def stop(self):
        self._ev.set()

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

    def run(self):
        """ Main connection loop for the AUV. """

        count = 0
        global_vars.log("Starting main connection loop.")
        while not self._ev.wait(timeout=constants.RECEIVE_SLEEP_DELAY):
            # time.sleep(RECEIVE_SLEEP_DELAY)

            # Always try to update connection status.
            if time.time() - self.time_since_last_ping > constants.CONNECTION_TIMEOUT:
                self.timeout()

            if self.radio is None or self.radio.is_open() is False:
                try:  # Try to connect to our devices.
                    self.radio = Radio(constants.RADIO_PATH)
                    global_vars.log("Radio device has been found!")
                except:
                    pass
            else:
                try:
                    # Read seven bytes (3 byte message, 4 byte checksum)
                    line = self.radio.read(7)
                    # self.radio.flush()

                    while(line != b'' and len(line) == 7):
                        intline = int.from_bytes(line, "big")
                        checksum = Crc32.confirm(intline)
                        if not checksum:
                            global_vars.log("invalid line***********************")
                            # self.radio.flush()
                            self.mc.update_motor_speeds([0, 0, 0, 0])
                            break

                        # message contains packet data without checksum
                        message = intline >> 32
                        if message == constants.PING:  # We have a ping!
                            self.ping_connected()
                            line = self.radio.read(7)
                            continue

                        print("NON-PING LINE READ WAS", bin(message))

                        # case block
                        header = message & 0xE00000

                        if header == constants.NAV_ENCODE:  # navigation
                            self.read_nav_command(message)

                        elif header == constants.XBOX_ENCODE:  # xbox navigation
                            self.read_xbox_command(message)

                        elif header == constants.DIVE_ENCODE:  # dive
                            desired_depth = message & 0b111111
                            print("We're calling dive command:", str(desired_depth))
                            constants.LOCK.acquire()
                            self.dive(desired_depth)
                            constants.LOCK.release()

                        elif header == constants.MISSION_ENCODE:  # mission/halt/calibrate/download data
                            self.read_mission_command(message)

                        elif header == constants.KILL_ENCODE:  # Kill/restart AUV threads
                            if (message & 1):
                                # Restart AUV threads
                                self.mc.zero_out_motors()
                                global_vars.restart_threads = True
                            else:
                                # Kill AUV threads
                                self.mc.zero_out_motors()
                                global_vars.stop_all_threads = True

                        line = self.radio.read(7)

                    # end while
                    self.radio.flush()

                except Exception as e:
                    global_vars.log("Error: " + str(e))
                    self.radio.close()
                    self.radio = None
                    global_vars.log("Radio is disconnected from pi!")
                    continue

            if(self.current_mission is not None):
                print(self.timer)
                self.current_mission.loop()

                # TODO statements because max time received
                self.timer = self.timer + 1
                if self.timer > constants.MAX_ITERATION_COUNT:
                    # kill mission, we exceeded time
                    self.abort_mission()

    def timeout(self):
        constants.LOCK.acquire()
        # Line read was EMPTY, but 'before' connection status was successful? Connection verification failed.
        if global_vars.connected is True:
            global_vars.log("Lost connection to BS.")

            # reset motor speed to 0 immediately and flush buffer
            self.mc.update_motor_speeds([0, 0, 0, 0])

            # monitor depth at surface
            # turn upwards motors on until we've reached okay depth range OR until radio is connected
            # have default be >0 to keep going up if pressure_sensor isn't there for some reason
            depth = 400  # number comes from depth of Isfjorden (not sure if this is actually where we'll be)

            # enforce check in case radio is not found
            if self.radio is not None:
                self.radio.flush()
            global_vars.connected = False
        depth = self.get_depth()
        # Turn upwards motors on until surface reached (if we haven't reconnected yet)
        if depth > 0:  # TODO: Decide on acceptable depth range
            self.mc.update_motor_speeds([0, 0, -25, -25])
        else:
            self.mc.update_motor_speeds([0, 0, 0, 0])
        constants.LOCK.release()

    def ping_connected(self):
        global_vars.log("PING")
        self.time_since_last_ping = time.time()

        constants.LOCK.acquire()
        if global_vars.connected is False:
            global_vars.log("Connection to BS verified.")
            global_vars.connected = True

            # TODO test case: set motor speeds
            data = [1, 2, 3, 4]
            self.x(data)
            # Halt disconnected resurfacing
            self.mc.update_motor_speeds([0, 0, 0, 0])
        constants.LOCK.release()

    def read_nav_command(self, message):
        x = (message & 0x01F600) >> 9
        sign = (message & 0x000100) >> 8
        y = (message & 0x0000FF)

        if (sign == 1):
            y = y * -1

        global_vars.log("Running motor command with (x, y): " + str(x) + "," + str(y))
        self.motor_queue.put((x, y, 0))

    def read_xbox_command(self, message):
        # xbox command
        vertical = (message & 0x10000)
        x = (message & 0x7F00) >> 8
        xsign = (message & 0x8000) >> 15
        y = message & 0x7F
        ysign = (message & 0x80) >> 7
        # Flip motors according to x and ysign
        if xsign != 1:
            x = -x
        if ysign != 1:
            y = -y
        #print("Xbox Command:", x, y)
        if vertical:
            self.motor_queue.put((x, y, 2))
        else:
            self.motor_queue.put((x, y, 1))

    def read_mission_command(self, message):
        x = message & 0b111
        global_vars.log("Mission encoding with (x): " + bin(x))
        if (x == 0) or (x == 1):
            # decode time
            t = message >> 3
            time_1 = t & 0b111111111

            # decode depth
            d = t >> 9
            depth = d & 0b111111

            print("Run mission:", x)
            print("with depth and time:", d, ",", time_1)

            # self.start_mission(x)  # 0 for mission 1, and 1 for mission 2 TODO
            # audioSampleMission() if x == 0 else mission2()
        if (x == 2):
            # halt
            print("HALT")
            self.mc.update_motor_speeds([0, 0, 0, 0])  # stop motors
            # Empty out motor queue
            while not self.motor_queue.empty():
                self.motor_queue.get()
            # send exit command to MotorQueue object
            self.halt[0] = True

        if (x == 3):
            print("CALIBRATE")

            depth = self.get_depth()
            global_vars.depth_offset = global_vars.depth_offset + depth
        if (x == 4):
            print("ABORT")
            # abort()
            pass
        if (x == 5):
            print("DOWNLOAD DATA")
            # downloadData()
            pass

    def start_mission(self, mission):
        """ Method that uses the mission selected and begin that mission """
        if(mission == 0):  # Echo-location.
            try:  # Try to start mission
                self.current_mission = Mission1(
                    self, self.mc, self.pressure_sensor, self.imu)
                self.timer = 0
                global_vars.log("Successfully started mission " + str(mission) + ".")
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
        global_vars.log("Successfully aborted the current mission.")
        # self.radio.write(str.encode("mission_failed()\n"))

    def timed_dive(self, time):

        self.motor_queue.queue.clear()
        self.mc.update_motor_speeds([0, 0, 0, 0])
        # wait until current motor commands finish running, will need global variable
        # Dive
        depth = self.get_depth()
        start_time = time.time()
        self.mc.update_motor_speeds([0, 0, constants.DEF_DIVE_SPD, constants.DEF_DIVE_SPD])
        # Time out and stop diving if > 1 min
        while time.time() < start_time + time:
            try:
                depth = self.get_depth()
                print("Succeeded on way down. Depth is", depth)
            except:
                print("Failed to read pressure going down")

        self.mc.update_motor_speeds([0, 0, 0, 0])
        # Wait 10 sec
        end_time = time.time() + 10  # 10 sec
        while time.time() < end_time:
            pass

        # clear radio
        self.radio.flush()
        for i in range(0, 3):
            self.radio.read(7)

        # Resurface
        self.mc.update_motor_speeds([0, 0, -constants.DEF_DIVE_SPD, -constants.DEF_DIVE_SPD])
        intline = 0
        while intline == 0:  # TODO: check what is a good surface condition
            line = self.radio.read(7)
            intline = int.from_bytes(line, "big") >> 32

            print(intline)
            try:
                depth = self.get_depth()
                print("Succeeded on way up. Depth is", depth)
            except:
                print("Failed to read pressure going up")
        self.mc.update_motor_speeds([0, 0, 0, 0])

    def dive(self, to_depth):
        self.motor_queue.queue.clear()
        self.mc.update_motor_speeds([0, 0, 0, 0])
        # wait until current motor commands finish running, will need global variable
        # Dive
        depth = self.get_depth()
        start_time = time.time()
        self.mc.update_motor_speeds([0, 0, constants.DEF_DIVE_SPD, constants.DEF_DIVE_SPD])
        # Time out and stop diving if > 1 min
        while depth < to_depth and time.time() < start_time + 60:
            try:
                depth = self.get_depth()
                print("Succeeded on way down. Depth is", depth)
            except:
                print("Failed to read pressure going down")

        self.mc.update_motor_speeds([0, 0, 0, 0])
        # Wait 10 sec
        end_time = time.time() + 10  # 10 sec
        while time.time() < end_time:
            pass

        self.radio.flush()
        for i in range(0, 3):
            self.radio.read(7)

        # Resurface
        self.mc.update_motor_speeds([0, 0, constants.DEF_DIVE_SPD, constants.DEF_DIVE_SPD])
        intline = 0
        while math.floor(depth) > 0 and intline == 0:  # TODO: check what is a good surface condition
            line = self.radio.read(7)
            intline = int.from_bytes(line, "big") >> 32

            print(intline)
            try:
                depth = self.get_depth()
                print("Succeeded on way up. Depth is", depth)
            except:
                print("Failed to read pressure going up")
        self.mc.update_motor_speeds([0, 0, 0, 0])

    def get_depth(self):
        if self.pressure_sensor is not None:
            pressure = 0
            try:
                self.pressure_sensor.read()
                pressure = self.pressure_sensor.pressure()
            except:
                print("Failed to read pressure sensor")

            # TODO: Check if this is accurate, mbars to m
            depth = (pressure-1013.25)/1000 * 10.2
            return depth
        else:
            global_vars.log("No pressure sensor found.")
            return None
