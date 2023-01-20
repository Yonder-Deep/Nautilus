from missions import *
from api import MotorQueue
from api import MotorController
from api import PressureSensor
from api import Crc32
from api import IMU
from api import Radio
from api import DiveController
from api import Hydrophone
from queue import Queue
from static import global_vars
from static import constants
from datetime import datetime
import math
import time
import os
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

    def __init__(self, queue, halt, pressure_sensor, imu, mc):
        self.pressure_sensor = pressure_sensor
        self.imu = imu
        self.mc = mc
        self.hydrophone = Hydrophone()
        self.time_since_last_ping = time.time() + 4
        self.diving = False
        self.current_mission = None
        self.timer = 0
        self.motor_queue = queue
        self.halt = halt               # List for MotorQueue to check updated halt status

        self.dive_controller = DiveController(self.mc, self.pressure_sensor, self.imu)

        self._ev = threading.Event()
        threading.Thread.__init__(self)

    def run(self):
        """ Constructor for the AUV """

        self._ev = threading.Event()

        threading.Thread.__init__(self)

    def stop(self):
        self._ev.set()

    # TODO delete

    def x(self, data):
        self.mc.update_motor_speeds(data)

    def test_motor(self, motor):
        """ Method to test all 4 motors on the AUV """

        # Update motion type for display on gui
        self.mc.motion_type = 4

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

            if global_vars.radio is None or global_vars.radio.is_open() is False:
                global_vars.connect_to_radio()
            else:
                try:
                    # Read seven bytes (3 byte message, 4 byte checksum)
                    line = global_vars.radio.read(7)

                    while(line != b''):
                        # print("large while")
                        if not global_vars.sending_data and len(line) == 7:
                            intline = int.from_bytes(line, "big")
                            checksum = Crc32.confirm(intline)
                            if not checksum:
                                global_vars.log("invalid line***********************")
                                # global_vars.radio.flush()
                                self.mc.update_motor_speeds([0, 0, 0, 0])
                                break

                            # message contains packet data without checksum
                            message = intline >> 32
                            if message == constants.PING:  # We have a ping!
                                self.ping_connected()
                                line = global_vars.radio.read(7)
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

                            elif header == constants.MANUAL_DIVE_ENCODE:
                                global_vars.movement_status = 2
                                seconds = message & 0b11111
                                back_speed = message & 0b111111100000
                                back_speed_sign = message & 0b1000000000000
                                front_speed = message & 0b11111110000000000000
                                front_speed_sign = message & 0b100000000000000000000

                                print("We're calling the manual dive command:", str(seconds), str(front_speed), str(back_speed))
                                constants.LOCK.acquire()
                                self.manual_dive(front_speed_sign, front_speed, back_speed_sign, back_speed, seconds)
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
                            elif header == constants.PID_ENCODE:
                                # Update a PID value in the dive controller
                                constant_select = (message >> 18) & 0b111
                                # Extract last 18 bits from message
                                # Map to smaller, more precise numbers later
                                value = message & (0x3FFFF)
                                print("Received PID Constant Select: {}".format(constant_select))
                                if (constant_select == 0b000):
                                    constants.P_PITCH = value
                                    self.dive_controller.update_pitch_pid()
                                elif (constant_select == 0b001):
                                    constants.I_PITCH = value
                                    self.dive_controller.update_pitch_pid()
                                elif (constant_select == 0b010):
                                    constants.D_PITCH = value
                                    self.dive_controller.update_pitch_pid()
                                elif (constant_select == 0b011):
                                    constants.P_DEPTH = value
                                    self.dive_controller.update_depth_pid()
                                elif (constant_select == 0b100):
                                    constants.I_DEPTH = value
                                    self.dive_controller.update_depth_pid()
                                elif (constant_select == 0b101):
                                    constants.D_DEPTH = value
                                    self.dive_controller.update_depth_pid()
                            line = global_vars.radio.read(7)
                        elif global_vars.sending_data:

                            # line = global_vars.radio.read(constants.FILE_SEND_PACKET_SIZE)
                            line = global_vars.radio.read(7)
                            print(line)
                            print("help me this ran though so that's")
                            global_vars.file_packets_received = int.from_bytes(line, "big")
                            self.data_connected()
                            global_vars.bs_response_sent = True

                    # end while
                    global_vars.radio.flush()

                except Exception as e:
                    global_vars.log("Error: " + str(e))
                    global_vars.radio.close()
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
            if global_vars.radio is not None:
                global_vars.radio.flush()
            global_vars.connected = False
        depth = self.get_depth()
        # Turn upwards motors on until surface reached (if we haven't reconnected yet)
        if depth is None or depth > 0:  # TODO: Decide on acceptable depth range
            self.mc.update_motor_speeds([0, 0, -25, -25])
        else:
            self.mc.update_motor_speeds([0, 0, 0, 0])
        constants.LOCK.release()

    def data_connected(self):
        global_vars.log("DATA PACKET")
        self.time_since_last_ping = time.time()

        constants.LOCK.acquire()
        if global_vars.connected is False:
            global_vars.log("Connection to BS verified.")
            global_vars.connected = True
            # Halt disconnected resurfacing
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
            global_vars.sending_data = True

            pass

    def start_mission(self, mission):
        """ Method that uses the mission selected and begin that mission """
        if(mission == 0):  # Echo-location.
            try:  # Try to start mission
                self.current_mission = Mission1(
                    self, self.mc, self.pressure_sensor, self.imu)
                self.timer = 0
                global_vars.log("Successfully started mission " + str(mission) + ".")
                # global_vars.radio.write(str.encode("mission_started("+str(mission)+")\n"))
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
        # global_vars.radio.write(str.encode("mission_failed()\n"))

    def manual_dive(self, front_speed_sign, front_speed, back_speed_sign, back_speed, time_dive):

        print(front_speed_sign, front_speed, back_speed_sign, back_speed, time_dive)

        front_speed = (-1) * front_speed if front_speed_sign == 0 else front_speed
        back_speed = (-1) * back_speed if back_speed_sign == 0 else back_speed

        time_begin = time.time()

        while time.time() - time_begin < time_dive:
            self.mc.update_motor_speeds([0, 0, 1.5*front_speed, 1.5*back_speed])
            try:
                depth = self.get_depth()
                print("Succeeded on way down. Depth is", depth)
            except:
                print("Failed to read pressure going down")

        self.mc.update_motor_speeds([0, 0, 0, 0])

        global_vars.radio.flush()

        for i in range(0, 3):
            global_vars.radio.read(7)

    def timed_dive(self, time):
        self.diving = True
        # Check if this path is actually right
        file_path = self.get_log_filename()
        log_file = open(file_path, "a")
        self.dive_log(log_file)

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
        global_vars.radio.flush()
        for i in range(0, 3):
            global_vars.radio.read(7)

        # Resurface
        self.mc.update_motor_speeds([0, 0, -constants.DEF_DIVE_SPD, -constants.DEF_DIVE_SPD])
        intline = 0
        while intline == 0:  # TODO: check what is a good surface condition
            line = global_vars.radio.read(7)
            intline = int.from_bytes(line, "big") >> 32

            print(intline)
            try:
                depth = self.get_depth()
                print("Succeeded on way up. Depth is", depth)
            except:
                print("Failed to read pressure going up")
        self.mc.update_motor_speeds([0, 0, 0, 0])
        self.diving = False
        log_file.close()

    def dive(self, to_depth):

        # self.diving = True
        # # Check if this path is actually right
        # file_path = self.get_log_filename()
        # log_file = open(file_path, "a")
        # self.dive_log(log_file)

        # self.motor_queue.queue.clear()

        # begin dive
        # self.dive_controller.start_dive(to_depth=to_depth, dive_length=10)

        # resurface
        # self.dive_controller.start_dive()
        '''
        # Wait 10 sec
        end_time = time.time() + 10  # 10 sec
        while time.time() < end_time:
            pass

        self.radio.flush()
        for i in range(0, 3):
            self.radio.read(7)

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
        '''
        # self.diving = False
        # log_file.close()
        # self.hydrophone.start_recording()
        # time.time.sleep(5)
        # self.hydrophone.stop_recording()

        # self.hydrophone.start_recording_for(5)
        global_vars.sending_data = True

    # Logs with depth calibration offset (heading may need to be merged in first)

    def dive_log(self, file):
        if self.diving:
            log_timer = threading.Timer(0.5, self.dive_log).start()
            file.write(time.time())  # might want to change to a more readable time format
            depth = self.get_depth() - global_vars.depth_offset
            file.write("Depth=" + str(depth))
            heading, roll, pitch = self.get_euler()
            file.write("Heading=" + str(heading))
            file.write("Pitch=" + str(pitch))

    # Does not include calibration offset
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

    # Does not include calibration offset
    def get_euler(self):
        try:
            heading, roll, pitch = self.imu.read_euler()
            # print('HEADING=', heading)
        except:
            # TODO print statement, something went wrong!
            heading, roll, pitch = None, None, None
        return heading, roll, pitch

    def get_log_filename(self):
        time_stamp = datetime.now().strftime('%Y-%m-%dT%H.%M.%S')
        filename = constants.LOG_FOLDER_PATH + time_stamp + ".txt"
        self.filename = filename
