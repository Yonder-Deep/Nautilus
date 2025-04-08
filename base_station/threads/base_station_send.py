import os
from platform import release

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


class BaseStation_Send(threading.Thread):
    def __init__(self, radio, in_q=None, out_q=None):
        """Initialize Serial Port and Class Variables
        debug: debugging flag"""

        # Instance variables
        self.joy = None
        self.in_q = in_q
        self.out_q = out_q
        self.manual_mode = True

        # Call super-class constructor
        threading.Thread.__init__(self)

        self.radio = radio

        # Try to connect our Xbox 360 controller.

        # XXX ---------------------- XXX ---------------------------- XXX TESTING AREA
        try:
            print("case0-----------------")
            self.joy = xbox.Joystick()
            print("case1")

            global_vars.log(self.out_q, "Successfuly found Xbox 360 controller.")
            print("case2")
        except:
            global_vars.log(self.out_q, "Warning: Cannot find xbox controller")

    # XXX ---------------------- XXX ---------------------------- XXX TESTING AREA

    def check_tasks(self):
        """This checks all of the tasks (given from the GUI thread) in our in_q, and evaluates them."""

        while not self.in_q.empty():
            task = "self." + self.in_q.get()
            # Try to evaluate the task in the in_q.
            try:
                eval(task)
            except Exception as e:
                print("Failed to evaluate in_q task: ", task)
                print("\t Error received was: ", str(e))

    def test_motor(self, motor, speed=10, duration=10):
        """Attempts to send the AUV a signal to test a given motor."""
        constants.lock.acquire()
        if not global_vars.connected:
            constants.lock.release()
            global_vars.log(
                self.out_q,
                "Cannot test "
                + motor
                + " motor(s) because there is no connection to the AUV.",
            )
        else:
            constants.lock.release()
            constants.radio_lock.acquire()

            if motor == "Forward":
                self.radio.write(
                    (constants.MOTOR_TEST_COMMAND << constants.HEADER_SHIFT)
                    | (0b000 << 13)
                    | (speed << 6)
                    | duration
                )
            elif motor == "Backward":
                self.radio.write(
                    (constants.MOTOR_TEST_COMMAND << constants.HEADER_SHIFT)
                    | (0b001 << 13)
                    | (speed << 6)
                    | duration
                )
            elif motor == "Down":
                self.radio.write(
                    (constants.MOTOR_TEST_COMMAND << constants.HEADER_SHIFT)
                    | (0b010 << 13)
                    | (speed << 6)
                    | duration
                )
            elif motor == "Left":
                self.radio.write(
                    (constants.MOTOR_TEST_COMMAND << constants.HEADER_SHIFT)
                    | (0b011 << 13)
                    | (speed << 6)
                    | duration
                )
            elif motor == "Right":
                self.radio.write(
                    (constants.MOTOR_TEST_COMMAND << constants.HEADER_SHIFT)
                    | (0b100 << 13)
                    | (speed << 6)
                    | duration
                )

            constants.radio_lock.release()

            global_vars.log(
                self.out_q, 'Sending encoded task: test_motor("' + motor + '")'
            )

    def test_heading(self):
        """Attempts to send the AUV a signal to test heading PID."""
        constants.lock.acquire()
        if not global_vars.connected:
            constants.lock.release()
            global_vars.log(
                self.out_q,
                "Cannot test heading because there is no connection to the AUV.",
            )
        else:
            constants.lock.release()
            global_vars.log(self.out_q, "Sending heading test")
            constants.radio_lock.acquire()
            self.radio.write(constants.TEST_HEADING_COMMAND << constants.HEADER_SHIFT)
            constants.radio_lock.release()

    def test_imu_calibration(self):
        """Sends AUV a signal to start imu calibration"""
        constants.lock.acquire()
        if not global_vars.connected:
            constants.lock.release()
            global_vars.log(
                self.out_q,
                "Cannot start imu calibration because there is no connection to the AUV.",
            )
        else:
            constants.lock.release()
            global_vars.log(self.out_q, "Sending imu calibration test...")
            constants.radio_lock.acquire()
            self.radio.write(constants.TEST_IMU_CALIBRATION << constants.HEADER_SHIFT)
            constants.radio_lock.release()


    def abort_mission(self):
        """Attempts to abort the mission for the AUV."""
        constants.lock.acquire()
        if not global_vars.connected:
            constants.lock.release()
            global_vars.log(
                self.out_q,
                "Cannot abort mission because there is no connection to the AUV.",
            )
        else:
            constants.lock.release()
            # self.radio.write("abort_mission()")
            global_vars.log(self.out_q, "Sending task: abort_mission()")
            self.manual_mode = True

    def start_mission(self, mission, depth, t):
        """Attempts to start a mission and send to AUV."""
        constants.lock.acquire()
        if global_vars.connected is False:
            constants.lock.release()
            global_vars.log(
                self.out_q,
                "Cannot start mission "
                + str(mission)
                + " because there is no connection to the AUV.",
            )
        else:
            constants.lock.release()
            depth = (depth << 12) & 0x3F000
            t = (t << 3) & 0xFF8
            constants.radio_lock.acquire()
            self.radio.write(
                (constants.MISSION_COMMAND << constants.HEADER_SHIFT)
                | depth
                | t
                | mission
            )
            print(
                bin(
                    (constants.MISSION_COMMAND << constants.HEADER_SHIFT)
                    | depth
                    | t
                    | mission
                )
            )

            constants.radio_lock.release()
            global_vars.log(
                self.out_q, "Sending task: start_mission(" + str(mission) + ")"
            )

    def send_halt(self):
        self.start_mission(constants.HALT_COMMAND, 0, 0)

    def send_controls(self, distance, angle):
        pass

    def send_calibrate_depth(self):
        self.start_mission(constants.CAL_DEPTH_COMMAND, 0, 0)

    def send_calibrate_heading(self):
        self.start_mission(constants.CAL_HEADING_COMMAND, 0, 0)

    def send_abort(self):
        self.start_mission(constants.ABORT_COMMAND, 0, 0)

    def send_download_data(self):
        self.start_mission(constants.DL_DATA_COMMAND, 0, 0)

    def send_dive(self, depth):
        constants.lock.acquire()
        if global_vars.connected is False:
            constants.lock.release()
            global_vars.log(
                self.out_q, "Cannot dive because there is no connection to the AUV."
            )
        else:
            constants.lock.release()
            constants.radio_lock.acquire()
            self.radio.write((constants.DIVE_COMMAND << constants.HEADER_SHIFT) | depth)
            print(bin((constants.DIVE_COMMAND << constants.HEADER_SHIFT) | depth))
            constants.radio_lock.release()
            global_vars.log(
                self.out_q, "Sending task: dive(" + str(depth) + ")"
            )  # TODO: change to whatever the actual command is called

    def send_packet_num(self):
        constants.radio_lock.acquire()
        # Currently using FILE_DL_PACKET_SIZE sized packets for sending num packets, though this is not really necessary
        # as the size is much larger than needed to send ints on this scale
        self.radio.write(
            global_vars.file_packets_received, constants.FILE_DL_PACKET_SIZE
        )
        print(global_vars.file_packets_received, constants.FILE_DL_PACKET_SIZE)
        constants.radio_lock.release()

    def send_pid_update(self, constant_select, value):
        # Update PID constants for the dive controller
        # constant_select: int storing which constant to update (0-2): pitch pid, (3-5): dive pid
        # value: what to update the constant to
        constants.lock.acquire()
        if global_vars.connected is False:
            constants.lock.release()
            global_vars.log(
                self.out_q,
                "Cannot update pid because there is no connection to the AUV.",
            )
        else:
            constants.lock.release()
            constant_select = constant_select << 18
            constants.radio_lock.acquire()
            self.radio.write(
                (constants.PID_COMMAND << constants.HEADER_SHIFT)
                | constant_select
                | value
            )
            print(
                bin(
                    (constants.PID_COMMAND << constants.HEADER_SHIFT)
                    | constant_select
                    | value
                )
            )
            constants.radio_lock.release()

    def send_dive_manual(self, front_motor_speed, rear_motor_speed, seconds):
        print(front_motor_speed, rear_motor_speed, seconds)
        constants.lock.acquire()
        if global_vars.connected is False:
            constants.lock.release()
            global_vars.log(
                self.out_q,
                "Cannot manual dive because there is no connection to the AUV.",
            )
        else:
            constants.lock.release()

            front_motor_speed_sign = 1 if front_motor_speed >= 0 else 0
            rear_motor_speed_sign = 1 if rear_motor_speed >= 0 else 0
            front_motor_speed_sign = (front_motor_speed_sign << 20) & 0x100000
            rear_motor_speed_sign = (rear_motor_speed_sign << 12) & 0x1000
            rear_motor_speed = (abs(rear_motor_speed) << 5) & 0xFE0
            front_motor_speed = (abs(front_motor_speed) << 13) & 0xFE000
            seconds = (seconds) & 0b11111
            print(
                front_motor_speed_sign,
                front_motor_speed,
                rear_motor_speed_sign,
                rear_motor_speed,
                seconds,
            )
            constants.radio_lock.acquire()

            self.radio.write(
                (constants.MANUAL_DIVE_COMMAND << constants.HEADER_SHIFT)
                | front_motor_speed_sign
                | front_motor_speed
                | rear_motor_speed_sign
                | rear_motor_speed
                | seconds
            )
            print(
                bin(
                    (constants.MANUAL_DIVE_COMMAND << constants.HEADER_SHIFT)
                    | front_motor_speed_sign
                    | front_motor_speed
                    | rear_motor_speed_sign
                    | rear_motor_speed
                    | seconds
                )
            )

            constants.radio_lock.release()
            global_vars.log(
                self.out_q,
                "Sending task: manual_dive("
                + str(front_motor_speed_sign)
                + ","
                + str(front_motor_speed)
                + ", "
                + str(rear_motor_speed_sign)
                + ","
                + str(rear_motor_speed)
                + ", "
                + str(seconds)
                + ")",
            )

    def encode_xbox(self, x, y, right_trigger):
        """Encodes a navigation command given xbox input."""
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
        return (
            (constants.XBOX_COMMAND << constants.HEADER_SHIFT)
            | vertical
            | xsign
            | xshift
            | ysign
            | y
        )

    def run(self):
        """Main sending threaded loop for the base station."""
        xbox_input = False

        # Begin our main loop for this thread.
        while True:
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
            #    global_vars.log(self.out_q,"Xbox controller has been disconnected.")
            #    self.joy = None

            # This executes if we never had a radio object, or it got disconnected.
            if self.radio is None or not global_vars.path_existance(
                constants.RADIO_PATHS
            ):
                # This executes if we HAD a radio object, but it got disconnected.
                if self.radio is not None and not global_vars.path_existance(
                    constants.RADIO_PATHS
                ):
                    global_vars.log(self.out_q, "Radio device has been disconnected.")
                    self.radio.close()

                # Try to assign us a new Radio object
                global_vars.connect_to_radio(self.out_q)
                self.radio = global_vars.radio

            # If we have a Radio object device, but we aren't connected to the AUV
            else:
                # Try to write line to radio.
                try:
                    # This is where secured/synchronous code should go.
                    constants.lock.acquire()
                    if (
                        global_vars.connected
                        and self.manual_mode
                        and not global_vars.downloading_file
                    ):
                        constants.lock.release()
                        if (
                            self.joy is not None
                            and self.joy.leftBumper()
                            and self.joy.rightBumper()
                        ):
                            # Read in potential kill-all/restart command
                            if self.joy.Guide():
                                # Send restart command
                                constants.radio_lock.acquire()
                                self.radio.write(
                                    (constants.KILL_COMMAND << constants.HEADER_SHIFT)
                                    | 1
                                )
                                constants.radio_lock.release()
                                print("Restarting AUV threads...")

                            elif self.joy.Back() and self.joy.Start():
                                # Send kill-all command
                                constants.radio_lock.acquire()
                                self.radio.write(
                                    (constants.KILL_COMMAND << constants.HEADER_SHIFT)
                                )
                                constants.radio_lock.release()
                                print("Killing AUV threads...")

                        if self.joy is not None and self.joy.A():
                            xbox_input = True

                            try:
                                print("[XBOX] X:", self.joy.leftX())
                                print("[XBOX] Y:", self.joy.leftY())
                                print("[XBOX] A\t")
                                print("[XBOX] Right Trigger:", self.joy.rightTrigger())

                                x = round(self.joy.leftX() * 100)
                                y = round(self.joy.leftY() * 100)
                                right_trigger = round(self.joy.rightTrigger() * 10)

                                self.out_q.put(
                                    "set_xbox_status(1," + str(right_trigger / 10) + ")"
                                )
                                print(
                                    "Right trigger pushed: Value is "
                                    + str(right_trigger)
                                )
                                navmsg = self.encode_xbox(x, y, right_trigger)

                                constants.radio_lock.acquire()
                                self.radio.write(navmsg)
                                constants.radio_lock.release()

                            except Exception as e:
                                global_vars.log(
                                    self.out_q, "Error with Xbox data: " + str(e)
                                )

                        # once A is no longer held, send one last zeroed out xbox command
                        if xbox_input and not self.joy.A():
                            constants.radio_lock.acquire()
                            self.radio.write(
                                (constants.XBOX_COMMAND << constants.HEADER_SHIFT)
                            )
                            constants.radio_lock.release()
                            print("[XBOX] NO LONGER A\t")
                            self.out_q.put(
                                "set_xbox_status(0,0)"
                            )  # updates gui that xbox controller no longer sending commands
                            xbox_input = False

                    elif global_vars.connected and global_vars.downloading_file:
                        constants.radio_lock.acquire()
                        if global_vars.packet_received:
                            self.send_packet_num()
                            global_vars.packet_received = False
                        constants.radio_lock.release()
                    else:
                        constants.lock.release()
                except Exception as e:
                    print(str(e))
                    self.radio.close()
                    self.radio = None
                    global_vars.log(self.out_q, "Radio device has been disconnected.")
                    continue
            time.sleep(constants.THREAD_SLEEP_DELAY)

    def mission_started(self, index):
        """When AUV sends mission started, switch to mission mode"""
        if index == 0:  # Echo location mission.
            self.manual_mode = False
            self.out_q.put("set_vehicle(False)")
            global_vars.log(self.out_q, "Switched to autonomous mode.")

        global_vars.log(self.out_q, "Successfully started mission " + str(index))

    def close(self):
        """Function that is executed upon the closure of the GUI (passed from input-queue)."""
        # close the xbox controller
        if self.joy is not None:
            self.joy.close()
        os._exit(1)  # => Force-exit the process immediately.
