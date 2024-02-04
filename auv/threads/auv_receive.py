from missions import *
from api import MotorController
from api import PressureSensor
from api import Crc32
from api import IMU
from api import Radio
from api import DiveController
from queue import LifoQueue
from queue import Queue
from static import global_vars
from static import constants
import math
import time
import os
import threading
import sys

from tests import heading_test as ht


sys.path.append("..")

# System imports

# Custom imports

# Responsibilites:
#   - receive data/commands
#   - update connected global variable


class AUV_Receive(threading.Thread):
    """Class for the AUV object. Acts as the main file for the AUV."""

    def __init__(
        self,
        queue,
        halt,
        pressure_sensor,
        imu,
        mc,
        gps,
        gps_q,
        in_q,
        out_q,
        auto_nav_thread,
    ):
        self.pressure_sensor = pressure_sensor
        self.imu = imu
        self.mc = mc
        self.gps = gps
        self.gps_q = gps_q
        self.time_since_last_ping = time.time() + 4
        self.diving = False
        self.current_mission = None
        self.timer = 0
        self.motor_queue = queue
        self.halt = halt  # List for MotorQueue to check updated halt status
        self.in_q = in_q
        self.out_q = out_q
        self.auto_nav_thread = auto_nav_thread
        self.dive_controller = DiveController(self.mc, self.pressure_sensor, self.imu)
        self._ev = threading.Event()
        threading.Thread.__init__(self)

    def run(self):
        """Constructor for the AUV"""

        self._ev = threading.Event()
        threading.Thread.__init__(self)

    def stop(self):
        self._ev.set()

    def test_motor(self, motor):
        """Method to test all 4 motors on the AUV"""
        print("TESTING MOTOR 1")
        # Update motion type for display on gui
        global_vars.movement_status = 4
        print(motor)
        if (
            motor == "FORWARD"
        ):  # Used to be LEFT motor, moves AUV forward (motor in back)
            self.mc.test_forward()
        elif (
            motor == "TURN"
        ):  # Used to be RIGHT MOTOR, moves AUV left or right (motor in front)
            self.mc.test_turn()
        elif motor == "FRONT":  # moves AUV down (front top motor)
            self.mc.test_front()
        elif motor == "BACK":  # moves AUV down (back top motor)
            self.mc.test_back()
        elif motor == "ALL":
            self.mc.test_all()
        else:
            raise Exception("No implementation for motor name: ", motor)

    def run(self):
        """Main connection loop for the AUV."""

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
                    line = global_vars.radio.read(
                        constants.COMM_BUFFER_WIDTH
                    )  # reads bytestring of desired packet size from the serial interface of the radio (radio recieves bytes over airwaves)

                    while (
                        line != b""
                    ):  # while bytes are still being read from the radio (radio is recieving information)
                        if not global_vars.sending_dive_log and len(line) == (
                            constants.COMM_BUFFER_WIDTH
                        ):
                            intline = int.from_bytes(
                                line, "big"
                            )  # converts the bytes into a binary string (integer) using big endian format
                            checksum = Crc32.confirm(
                                intline
                            )  # checks if the encapsulated packet is valid using cyclical redundacy check
                            if not checksum:
                                global_vars.log(
                                    "invalid line***********************"
                                )  # the binary string is invalid
                                print(bin(intline))  # prints the invalid line
                                self.mc.update_motor_speeds([0, 0, 0, 0])
                                break

                            message = (
                                intline >> 32
                            )  # removes the CRC encoding from the message
                            if message == constants.PING:  # The message is a PING!
                                self.ping_connected()  # sets connection status to True
                                line = global_vars.radio.read(
                                    constants.COMM_BUFFER_WIDTH
                                )  # reads a new line from the radio so that cycle can start again
                                continue

                            print(
                                "NON-PING LINE READ WAS", bin(message)
                            )  # if our message is not a ping

                            # case block
                            header = message >> constants.HEADER_SHIFT

                            if header == constants.MOTOR_TEST_COMMAND:  # motor-testing
                                global_vars.movement_status = 2
                                test = (message >> 13) & 0b111
                                speed = (message >> 6) & 0b1111111
                                duration = message & 0b111111

                                print("motor test command received")
                                constants.LOCK.acquire()
                                self.read_motor_test_command(test, speed, duration)
                                constants.LOCK.release()

                            elif header == constants.XBOX_COMMAND:  # xbox navigation
                                # Update motion type for display on gui
                                global_vars.movement_status = 1
                                self.read_xbox_command(message)

                            elif header == constants.NAV_COMMAND:  # navigation
                                print("nav command read")
                                # Update motion type for display on gui
                                global_vars.movement_status = 2
                                self.read_nav_command(message)

                            elif (
                                header == constants.TEST_HEADING_COMMAND
                            ):  # testing heading
                                print("testing heading command read")
                                heading_test = ht.Heading_Test()
                                heading_test.init()
                                global_vars.log("Starting heading test")
                                heading_test.start()

                            elif header == constants.DIVE_COMMAND:  # dive
                                # Update motion type for display on gui
                                global_vars.movement_status = 2
                                desired_depth = message & 0b111111
                                print("We're calling dive command:", str(desired_depth))
                                constants.LOCK.acquire()
                                self.dive(desired_depth)
                                constants.LOCK.release()

                            elif header == constants.MANUAL_DIVE_COMMAND:
                                global_vars.movement_status = 2
                                seconds = message & 0b11111
                                back_speed = (message & 0b111111100000) >> 5
                                back_speed_sign = (message & 0b1000000000000) >> 12
                                front_speed = (message & 0b11111110000000000000) >> 13
                                front_speed_sign = (
                                    message & 0b100000000000000000000
                                ) >> 20

                                print(
                                    "We're calling the manual dive command:",
                                    str(seconds),
                                    str(front_speed),
                                    str(back_speed),
                                )
                                constants.LOCK.acquire()
                                self.manual_dive(
                                    front_speed_sign,
                                    front_speed,
                                    back_speed_sign,
                                    back_speed,
                                    seconds,
                                )
                                constants.LOCK.release()

                            elif (
                                header == constants.MISSION_COMMAND
                            ):  # mission/halt/calibrate/download data
                                self.read_mission_command(message)

                            elif (
                                header == constants.KILL_COMMAND
                            ):  # Kill/restart AUV threads
                                if message & 1:
                                    # Restart AUV threads
                                    self.mc.zero_out_motors()
                                    global_vars.restart_threads = True
                                else:
                                    # Kill AUV threads
                                    self.mc.zero_out_motors()
                                    global_vars.stop_all_threads = True

                            elif header == constants.PID_COMMAND:
                                # Update a PID value in the dive controller
                                constant_select = (message >> 18) & 0b111
                                # Extract last 18 bits from message
                                # Map to smaller, more precise numbers later
                                value = message & (0x3FFFF)
                                print(
                                    "Received PID Constant Select: {}".format(
                                        constant_select
                                    )
                                )
                                if constant_select == 0b000:
                                    constants.P_PITCH = value
                                    self.dive_controller.update_pitch_pid()
                                elif constant_select == 0b001:
                                    constants.I_PITCH = value
                                    self.dive_controller.update_pitch_pid()
                                elif constant_select == 0b010:
                                    constants.D_PITCH = value
                                    self.dive_controller.update_pitch_pid()
                                elif constant_select == 0b011:
                                    constants.P_DEPTH = value
                                    self.dive_controller.update_depth_pid()
                                elif constant_select == 0b100:
                                    constants.I_DEPTH = value
                                    self.dive_controller.update_depth_pid()
                                elif constant_select == 0b101:
                                    constants.D_DEPTH = value
                                    self.dive_controller.update_depth_pid()

                            global_vars.radio.flush()

                            line = global_vars.radio.read(constants.COMM_BUFFER_WIDTH)
                            continue

                        else:  # basically if global_vars.sending_dive_log:
                            print("sending data")
                            line = global_vars.radio.read(
                                constants.FILE_SEND_PACKET_SIZE
                            )
                            global_vars.file_packets_received = int.from_bytes(
                                line, "big"
                            )
                            global_vars.bs_response_sent = True
                            global_vars.sending_dive_log = False

                    # end while
                    global_vars.radio.flush()

                except Exception as e:
                    global_vars.log("Error: " + str(e))
                    global_vars.radio.close()
                    global_vars.log("Radio is disconnected from pi!")
                    continue

            if self.current_mission is not None:
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
            # self.mc.update_motor_speeds([0, 0, -25, -25])
            self.mc.update_motor_speeds(
                [0, 0, 0, 0]
            )  # TODO change this back, only done to avoid motor damage
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

            # Halt disconnected resurfacing
            self.mc.update_motor_speeds([0, 0, 0, 0])
        constants.LOCK.release()

    def read_nav_command(self, message):
        x = (message & 0x01F600) >> 9
        sign = (message & 0x000100) >> 8
        y = message & 0x0000FF

        if sign == 1:
            y = y * -1
        print("Nav command read")
        global_vars.log("Running motor command with (x, y): " + str(x) + "," + str(y))
        self.motor_queue.put((x, y, 0))

    def read_motor_test_command(self, test, speed, duration):
        forward_speed = 0
        turn_speed = 0
        down_speed = 0

        if test == 0:  # forward
            forward_speed = speed
        elif test == 1:  # reverse
            forward_speed = -1 * speed
        elif test == 2:  # down
            down_speed = speed
        elif test == 3:  # left
            turn_speed = -1 * speed
        elif test == 4:  # right
            turn_speed = speed

        time_begin = time.time()

        while time.time() - time_begin < duration:
            self.mc.update_motor_speeds(
                [
                    forward_speed,
                    turn_speed,
                    down_speed,
                    down_speed,
                ]
            )
            try:
                depth = self.get_depth()
                print("Succeeded on way down. Depth is", depth)
            except:
                print("Failed to read pressure going down")

        self.mc.update_motor_speeds([0, 0, 0, 0])

        global_vars.radio.flush()

        for i in range(0, 3):
            global_vars.radio.read(constants.COMM_BUFFER_WIDTH)

    def read_xbox_command(self, message):
        # xbox command
        vertical = message & 0x10000
        x = (message & 0x7F00) >> 8
        xsign = (message & 0x8000) >> 15
        y = message & 0x7F
        ysign = (message & 0x80) >> 7
        # Flip motors according to x and ysign
        if xsign != 1:
            x = -x
        if ysign != 1:
            y = -y
        # print("Xbox Command:", x, y)
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
        if x == 2 or x == 4:
            # halt
            print("HALT")
            self.mc.update_motor_speeds([0, 0, 0, 0])  # stop motors
            # Empty out motor queue
            while not self.motor_queue.empty():
                self.motor_queue.get()
            # send exit command to MotorQueue object
            self.halt[0] = True

        if x == 3:
            print("CALIBRATE DEPTH")

            depth = self.get_depth()
            global_vars.depth_offset = global_vars.depth_offset + depth

        if x == 5:
            print("DOWNLOAD DATA")
            global_vars.sending_dive_log = True
            pass

        if x == 6:
            print("CALIBRATE HEADING")

            heading = self.get_heading()
            global_vars.heading_offset = (global_vars.heading_offset + heading) % 360

    def start_mission(self, mission):
        """Method that uses the mission selected and begin that mission"""
        if mission == 0:  # Echo-location.
            try:  # Try to start mission
                self.current_mission = Mission1(
                    self, self.mc, self.pressure_sensor, self.imu
                )
                self.timer = 0
                global_vars.log("Successfully started mission " + str(mission) + ".")
                # global_vars.radio.write(str.encode("mission_started("+str(mission)+")\n"))
            except Exception as e:
                raise Exception(
                    "Mission " + str(mission) + " failed to start. Error: " + str(e)
                )
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

    def manual_dive(
        self, front_speed_sign, front_speed, back_speed_sign, back_speed, time_dive
    ):
        print(front_speed_sign, front_speed, back_speed_sign, back_speed, time_dive)

        front_speed = (-1) * front_speed if front_speed_sign == 0 else front_speed
        back_speed = (-1) * back_speed if back_speed_sign == 0 else back_speed

        time_begin = time.time()

        while time.time() - time_begin < time_dive:
            self.mc.update_motor_speeds(
                [
                    0,
                    0,
                    1.5 * front_speed,
                    1.5 * back_speed,
                ]
            )
            try:
                depth = self.get_depth()
                print("Succeeded on way down. Depth is", depth)
            except:
                print("Failed to read pressure going down")

        self.mc.update_motor_speeds([0, 0, 0, 0])

        global_vars.radio.flush()

        for i in range(0, 3):
            global_vars.radio.read(constants.COMM_BUFFER_WIDTH)

    def timed_dive(self, time):
        self.diving = True
        # Check if this path is actually right
        file_path = os.path.dirname(os.path.dirname(__file__)) + "logs/dive_log.txt"
        log_file = open(file_path, "a")
        self.dive_log(log_file)

        self.motor_queue.queue.clear()
        self.mc.update_motor_speeds([0, 0, 0, 0])
        # wait until current motor commands finish running, will need global variable
        # Dive
        depth = self.get_depth()
        start_time = time.time()
        self.mc.update_motor_speeds(
            [0, 0, constants.DEF_DIVE_SPD, constants.DEF_DIVE_SPD]
        )
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
            global_vars.radio.read(constants.COMM_BUFFER_WIDTH)

        # Resurface
        self.mc.update_motor_speeds(
            [0, 0, -constants.DEF_DIVE_SPD, -constants.DEF_DIVE_SPD]
        )
        intline = 0
        while intline == 0:  # TODO: check what is a good surface condition
            line = global_vars.radio.read(constants.COMM_BUFFER_WIDTH)
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
        self.diving = True
        # Check if this path is actually right
        file_path = (
            os.path.dirname(os.path.dirname(__file__)) + "logs/" + constants.DIVE_LOG
        )
        log_file = open(file_path, "a")
        self.dive_log(log_file)

        self.motor_queue.queue.clear()

        # begin dive
        self.dive_controller.start_dive(to_depth=to_depth, dive_length=10)

        # resurface

        self.dive_controller.start_dive()

        # Wait 10 sec
        end_time = time.time() + 10  # 10 sec
        while time.time() < end_time:
            pass

        global_vars.radio.flush()
        for i in range(0, 3):
            global_vars.radio.read(constants.COMM_BUFFER_WIDTH)

        intline = 0
        while (
            math.floor(depth) > 0 and intline == 0
        ):  # TODO: check what is a good surface condition
            line = global_vars.radio.read(constants.COMM_BUFFER_WIDTH)
            intline = int.from_bytes(line, "big") >> 32

            print(intline)
            try:
                depth = self.get_depth()
                print("Succeeded on way up. Depth is", depth)
            except:
                print("Failed to read pressure going up")
        self.diving = False
        log_file.close()

    # Logs with depth calibration offset (heading may need to be merged in first)
    def dive_log(self, file):
        if self.diving:
            # log_timer = threading.Timer(0.5, self.dive_log).start()
            file.write(
                str(time.time())
            )  # might want to change to a more readable time format
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
            depth = (pressure - 1013.25) / 1000 * 10.2
            # return depth - global_vars.depth_offset()
            return depth
        else:
            global_vars.log("No pressure sensor found.")
            return None

    def get_heading(self):
        if self.imu is not None:
            try:
                heading, _, _ = self.imu.read_euler()
            except:
                print("Failed to read IMU")
            return heading - global_vars.heading_offset
        else:
            global_vars.log("No IMU found.")
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

    def start_heading_test(self, set_heading=0):
        """Method to start the heading test"""
        motor_q = LifoQueue()
        halt = False
        pressure_sensor = None
        imu = None
        motors = []
        gps = None
        gps_q = None
        depth_cam = None
        in_q = None
        out_q = None
        heading_pid = None

        # Create an instance of Heading_Test
        heading_test_instance = Heading_Test(
            motor_q,
            halt,
            pressure_sensor,
            imu,
            motors,
            gps,
            gps_q,
            depth_cam,
            in_q,
            out_q,
            heading_pid,
        )

        # Call run from heading_test
        heading_test_instance.run(set_heading)
