
from numpy import arctan2, sin, cos, degrees, radians
from api import PID
from static import constants


class Heading_Test(threading.Thread):
        def __init__(
        self,
        motor_q,
        halt,
        pressure_sensor,
        imu,
        mc,
        gps,
        gps_q,
        depth_cam,
        in_q,
        out_q,
    ):
        self.dest_longitude = None
        self.dest_latitude = None
        self.curr_longitude = None
        self.curr_latitude = None
        self.curr_accel = None
        self.motor_q = motor_q
        self.halt = halt
        self.pressure_sensor = pressure_sensor
        self.imu = imu
        self.mc = mc
        self.gps = gps
        self.gps_connected = True if gps is not None else False
        self.gps_q = gps_q
        self.gps_speed_stack = LifoQueue()
        self.depth_cam = depth_cam
        self.in_q = in_q
        self.out_q = out_q

    def update_motor():
        "update motor speed according to PID"
        heading, roll, pitch = self.imu.read_euler()
        self.mc.pid_motor(heading)

        # updates the motor speed - add PID value to motor speed
    
    def run(self, set_heading):
        self.heading_pid = PID(self.mc, 0, 5, 0.1, debug=True, name="Heading", p=constants.P_HEADING, i=constants.I_HEADING, d=constants.D_HEADING)

        # 1) start the motor at some speed (maybe MAX_SPEED)
        current_heading =  # set to current heading

        while current_heading != 0:
            
            update_motor()
            # update current_heading

            # check if current_heading is north/0 for 5 seconds. If so, break
            break
        
        # stop motors

def calculate_direction(lat1, long1, lat2, long2):
    """Uses forward azimuth calculation to determine bearing"""
    lat1 = radians(lat1)
    long1 = radians(long1)
    lat2 = radians(lat2)
    long2 = radians(long2)
    dL = long2 - long1
    X = cos(lat2) * sin(dL)
    Y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dL)
    bearing = arctan2(X, Y)
    direction = (degrees(bearing) + 360) % 360
    return direction


def calculate_distance():
    distance = 0
    return distance


if __name__ == "__main__":
    direction = calculate_direction(32.883233, -117.235239, 32.883404, -117.235400)
    print(direction)
