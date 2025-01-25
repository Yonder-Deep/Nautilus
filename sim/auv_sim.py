from gz.msgs10.double_pb2 import Double
from gz.msgs10.imu_pb2 import IMU
from gz.msgs10.navsat_pb2 import NavSat
from gz.msgs10.vector3d_pb2 import Vector3d
from gz.transport13 import Node
import numpy as np
 
import time

def main():
    node = Node()
    
    # Add a current
    current_topic = "/ocean_current"
    pub_current = node.advertise(current_topic, Vector3d)
    
    current_msg = Vector3d()
    current_msg.x = 0.2
    current_msg.y = 0
    current_msg.z = 0
    
    # For motor control
    forward_thrust_topic = "/model/tethys/joint/propeller_joint/cmd_thrust"
    pub_forward_thrust = node.advertise(forward_thrust_topic, Double)
 
    double_msg = Double()
    double_msg.data = 0
    
    # For sensors
    imu_topic = "/imu"
    gps_topic = "/navsat"

    if node.subscribe(IMU, imu_topic, imu_cb):
        print("Subscribing to type {} on topic [{}]".format(
            IMU, imu_topic))
    else:
        print("Error subscribing to topic [{}]".format(imu_topic))
        return
 
    if node.subscribe(NavSat, gps_topic, gps_cb):
        print("Subscribing to type {} on topic [{}]".format(
            NavSat, gps_topic))
    else:
        print("Error subscribing to topic [{}]".format(gps_topic))
        return
 
    # wait for shutdown
    try:
        while True:
            if not pub_forward_thrust.publish(double_msg):
                break
            print("Publishing 'Thrust' on topic [{}]".format(forward_thrust_topic))
          
            if not pub_current.publish(current_msg):
                break
            print("Publishing 'Current' on topic [{}]".format(current_topic))
            time.sleep(0.01)
          
    except KeyboardInterrupt:
        pass
    print("Done")
    
# Returns standard RPY convention 
def quaternion_to_euler(x, y, z, w):
    ysqr = y * y

    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + ysqr)
    X = np.degrees(np.arctan2(t0, t1))

    t2 = +2.0 * (w * y - z * x)

    t2 = np.clip(t2, a_min=-1.0, a_max=1.0)
    Y = np.degrees(np.arcsin(t2))

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (ysqr + z * z)
    Z = np.degrees(np.arctan2(t3, t4))

    return X, Y, Z 

def imu_cb(msg: IMU):
    raw_quaternion = msg.orientation
    raw_angular_velocity = msg.angular_velocity
    raw_linear_acceleration = msg.linear_acceleration
    
    roll, pitch, yaw = quaternion_to_euler(raw_quaternion.x, raw_quaternion.y, 
                                           raw_quaternion.z, raw_quaternion.w)
    x, y, z = raw_angular_velocity.x, raw_angular_velocity.y, raw_angular_velocity.z
    lx, ly, lz = raw_linear_acceleration.x, raw_linear_acceleration.y, raw_linear_acceleration.z
    
    print("Roll {}, Pitch {}, Yaw {}".format(roll, pitch, yaw))
    print(msg)

def gps_cb(msg: NavSat):
    latitude = msg.latitude_deg
    longitude = msg.longitude_deg
    print("Latitude {}, Longitude {}".format(latitude, longitude))
    print(msg)

if __name__ == "__main__":
    main()
 