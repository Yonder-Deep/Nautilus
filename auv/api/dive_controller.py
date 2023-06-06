from api import PID
import time
from static import global_vars
from static import constants


class DiveController:
    def __init__(self, mc, pressure_sensor, imu):
        self.mc = mc
        self.pressure_sensor = pressure_sensor
        self.imu = imu
        self.pid_pitch = PID(mc, 0, 5, 0.1, debug=True, name="Pitch", p=constants.P_PITCH, i=constants.I_PITCH, d=constants.D_PITCH)
        self.pid_depth = PID(mc, 0, 0.2, 0.1, debug=True, name="Depth", p=constants.P_DEPTH, i=constants.I_DEPTH, d=constants.D_DEPTH)
        self.pid_heading = PID(mc, 0, 5, 0.1, debug=True, name="Heading", p=constants.P_HEADING, i=constants.I_HEADING, d=constants.D_HEADING)

    def get_depth(self):
        if self.pressure_sensor is not None:
            while(True):
                try:
                    self.pressure_sensor.read()
                    break
                except:
                    continue
            pressure = self.pressure_sensor.pressure()
            # TODO: Check if this is accurate, mbars to m
            depth = (pressure-1013.25)/1000 * 10.2
            return depth - global_vars.depth_offset
        else:
            global_vars.log("No pressure sensor found.")
            return None

    # note: default arguments are to resurface
    def start_dive(self, to_depth=0, dive_length=0):
        self.pid_depth.update_target(to_depth)

        self.mc.update_motor_speeds([0, 0, 0, 0])
        # wait until current motor commands finish running, will need global variable
        # Dive

        depth = self.get_depth()
        start_heading, _, _ = self.imu.read_euler()
        start_time = time.time()

        target_met = False
        target_met_time = 0

        # modulo: a mod function that retains negatives (ex. -1 % 360 = -1)

        def modulo(x, y): return x % y if x > 0 else -1 * (abs(x) % y)

        # turn_error: Calculates distance between target and heading angles
        # modulo(target - heading, 360) -> absolute distance between both angles
        # needed because imu only contains 0-360 degrees, need to account for
        # negative angles and angles > 360
        def turn_error(target, heading): return modulo(target - heading, 360)

        # main PID loop?
        # Time out and stop diving if > 1 min
        while time.time() < start_time + 60:
            try:
                depth = self.get_depth()

            except:
                print("Dive controller: Failed to read pressure")
                time.sleep(0.1)
                continue

            try:
                heading, _, pitch = self.imu.read_euler()
            except:
                print("Dive controller: Failed to read IMU value")
                time.sleep(0.1)
                continue

            depth_correction = self.pid_depth.pid(depth)
            pitch_correction = self.pid_pitch.pid(pitch)
            heading_correction = self.pid_heading.pid(turn_error(start_heading, heading))

            if depth_correction - abs(pitch_correction) < -150:
                depth_correction = -150 + abs(pitch_correction)
            if depth_correction + abs(pitch_correction) > 150:
                depth_correction = 150 - abs(pitch_correction)

            front_motor_value = depth_correction - pitch_correction
            back_motor_value = depth_correction + pitch_correction
            side_motor_value = heading_correction

            print("Depth_Correction: {}\tPitch_Correction: {}\tHeading_Correction: {}\n".format(depth_correction, pitch_correction, heading_correction))
            print("Current time elapsed: {}".format(time.time() - start_time))

            # NOTE: check side_motor_value to see if the sign is correct
            #self.mc.update_motor_speeds([min(side_motor_value,100), max(-side_motor_value,-100), min(back_motor_value,100), min(front_motor_value,100)])
            try:
                self.mc.update_motor_speeds([side_motor_value, -side_motor_value, back_motor_value, front_motor_value])
            except:
                print("Could not update motor speeds, argument out of range")

            if self.pid_depth.within_tolerance and not target_met:
                # want to wait for dive_length seconds before stopping
                target_met = True
                target_met_time = time.time()

            if target_met and time.time() > target_met_time + dive_length:
                print("Maintained depth for {} seconds, ending dive".format(dive_length))
                break

            print("Currently diving. Current depth: {}, Target depth: {}".format(depth, to_depth))
            time.sleep(0.1)

        self.mc.update_motor_speeds([0, 0, 0, 0])

    def update_pitch_pid(self):
        self.pid_pitch = PID(self.mc, 0, 5, 0.1, debug=True, name="Pitch", p=constants.P_PITCH, i=constants.I_PITCH, d=constants.D_PITCH)
        print("Updating pitch PID constants: {} {} {}".format(constants.P_PITCH, constants.I_PITCH, constants.D_PITCH))

    def update_depth_pid(self):
        self.pid_depth = PID(self.mc, 0, 0.2, 0.1, debug=True, name="Depth", p=constants.P_DEPTH, i=constants.I_DEPTH, d=constants.D_DEPTH)
        print("Updating depth PID constants: {} {} {}".format(constants.P_DEPTH, constants.I_DEPTH, constants.D_DEPTH))

    def update_heading_pid(self):
        self.pid_heading = PID(self.mc, 0, 5, 0.1, debug=True, name="Heading", p=constants.P_HEADING, i=constants.I_HEADING, d=constants.D_HEADING)
        print("Updating heading PID constants: {} {} {}".format(constants.P_HEADING, constants.I_HEADING, constants.D_HEADING))
