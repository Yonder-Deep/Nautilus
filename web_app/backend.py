# System imports
import serial
import time
import threading
from queue import Queue

# Custom imports
from api import Radio

from static import constants
from static import global_vars


class Backend(threading.Thread):
    def __init__(self, radio, in_q=None):
        super().__init__()
        self.radio = radio
        self.in_q = in_q
        self._stop_event = threading.Event()

    def test_motor(self, motor, speed=10, duration=10):
        """Attempts to send the AUV a signal to test a given motor."""
        speed = int(speed)
        duration = int(duration)
        if not global_vars.connected:
            print("Cannot run motor because no connection to AUV")
        else:
            constants.radio_lock.acquire()
            if motor == "Forward":
                self.radio.write(
                    (constants.MOTOR_TEST_COMMAND << constants.HEADER_SHIFT)
                    | (0b000 << 13)
                    | (speed << 6)
                    | duration
                )
                print("done sending")
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

    def test_heading(self, target, duration):
        """Attempts to send the AUV a signal to test heading PID."""
        constants.lock.acquire()
        if not global_vars.connected:
            print("Cannot test heading because there is no connection to the AUV.")
        else:
            print("Sending heading test")
            constants.radio_lock.acquire()
            self.radio.write(constants.TEST_HEADING_COMMAND << constants.HEADER_SHIFT)
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

    def send_calibrate_depth(self):
        self.start_mission(constants.CAL_DEPTH_COMMAND, 0, 0)

    def send_calibrate_heading(self):
        self.start_mission(constants.CAL_HEADING_COMMAND, 0, 0)

    def send_abort(self):
        self.start_mission(constants.ABORT_COMMAND, 0, 0)

    def send_download_data(self):
        self.start_mission(constants.DL_DATA_COMMAND, 0, 0)

    def manual_dive(self, front_motor_speed, rear_motor_speed, seconds):
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

    def mission_started(self, index):
        """When AUV sends mission started, switch to mission mode"""
        if index == 0:  # Echo location mission.
            self.manual_mode = False
            self.out_q.put("set_vehicle(False)")
            global_vars.log(self.out_q, "Switched to autonomous mode.")

        global_vars.log(self.out_q, "Successfully started mission " + str(index))

    def run(self):
        while not self._stop_event.is_set():
            try:
                command = self.in_q.get(timeout=1)
                if command is not None:
                    command()
            except:
                pass
            time.sleep(constants.THREAD_SLEEP_DELAY)

    def stop(self):
        self._stop_event.set()
        self.in_q.put(None)

    def join(self, timeout=None):
        self.stop()
        super(Backend, self).join(timeout)
