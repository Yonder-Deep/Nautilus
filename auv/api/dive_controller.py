from api import PID
import time


class DiveController:
    def __init__(self, mc, pressure_sensor, imu):
        self.mc = mc
        self.pressure_sensor = pressure_sensor
        self.imu = imu
        self.pid_pitch = PID(mc, 0, 5, 0.1, debug=True, p=5.0)
        self.pid_depth = PID(mc, 0, 0.2, 0.1, debug=True, p=5.0)


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

    def start_dive(self, to_depth):
        self.pid_depth.update_target(to_depth)

        self.mc.update_motor_speeds([0, 0, 0, 0])
        # wait until current motor commands finish running, will need global variable
        # Dive

        depth = self.get_depth()
        start_time = time.time()
        # main PID loop? 
        # Time out and stop diving if > 1 min
        while depth < to_depth and time.time() < start_time + 60:
            try:
                depth = self.get_depth()
                
            except:
                print("Failed to read pressure going down")
                return

            try:
                _, pitch,_ = self.imu.read_euler()
            except:
                print("Failed to read IMU value going down")
                return

            depth_correction = self.pid_depth.pid(depth)
            pitch_correction = self.pid_pitch.pid(pitch)
            front_motor_value = depth_correction - pitch_correction
            back_motor_value = depth_correction + pitch_correction
            print("Front Motor Value: {}".format(front_motor_value))
            print("Back Motor value: {}".format(back_motor_value))
            self.mc.update_motor_speeds([0, 0, back_motor_value, front_motor_value])
            print("Succeeded on way down. Depth is", depth)

        self.mc.update_motor_speeds([0, 0, 0, 0])

