from api import PID
import time


class DiveController:
    def __init__(self, mc, pressure_sensor, imu):
        self.mc = mc
        self.pressure_sensor = pressure_sensor
        self.imu = imu
        self.pid_pitch = PID(mc, 0, 5, 0.1, debug=True, p=5.0)
        self.pid_depth = PID(mc, 0, 0.2, 0.1, debug=True, p=10.0)


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
            return depth
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
        start_time = time.time()

        target_met = False
        target_met_time = 0
        # main PID loop?
        # Time out and stop diving if > 1 min
        while time.time() < start_time + 300:
            try:
                depth = self.get_depth()

            except:
                print("Dive controller: Failed to read pressure")
                time.sleep(0.1)
                continue

            try:
                _, pitch, _ = self.imu.read_euler()
            except:
                print("Dive controller: Failed to read IMU value")
                time.sleep(0.1)
                continue

            depth_correction = self.pid_depth.pid(depth)
            pitch_correction = self.pid_pitch.pid(pitch)
            front_motor_value = depth_correction - pitch_correction
            back_motor_value = depth_correction + pitch_correction
            print("Front Motor Value: {} \nBack Motor Value: {}".format(front_motor_value, back_motor_value))
            self.mc.update_motor_speeds([0, 0, back_motor_value, front_motor_value])

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
