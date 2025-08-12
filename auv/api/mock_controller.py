try:
    from .abstract import AbstractController
except:
    import sys
    sys.path.append("..")
    from abstract import AbstractController
from models.data_types import State, InitialState, SerialState, MotorSpeeds

from time import time
from threading import Lock
import numpy as np
from numpy import ndarray as arr
from numpy import float64 as f64
from scipy.spatial.transform import Rotation as R
from scipy.integrate import solve_ivp

def quaternion_multiply(q1, q2):
    """
    Multiplies two quaternions (x, y, z, w).

    Args:
        q1: A numpy array representing the first quaternion [x, y, z, w].
        q2: A numpy array representing the second quaternion [x, y, z, w].

    Returns:
        A numpy array representing the product of the two quaternions [x, y, z, w].
    """
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
    z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
    return np.array([x, y, z, w])

def quaternion_derivative(q, omega):
    """
    Calculates the derivative of a quaternion (x, y, z, w) given angular velocity.

    Args:
        q: A numpy array representing the quaternion [x, y, z, w].
        omega: A numpy array representing the angular velocity [wx, wy, wz].

    Returns:
        A numpy array representing the quaternion derivative [x, y, z, w].
    """
    omega_q = np.array([omega[0], omega[1], omega[2], 0])  # Pure quaternion
    q_dot = 0.5 * quaternion_multiply(omega_q, q)
    return q_dot

def pack(unpacked: list[arr]) -> arr:
    """ Inverse of unpack(). Takes an unpacked list of state arrays and flattens
        the state arrays into a single state array of 13 indices.
    """
    return np.concatenate(
        (unpacked[0], unpacked[1], unpacked[2], unpacked[3]),
        axis=None)

def unpack(packed: arr) -> list[arr]:
    """ Inverse of pack(). Takes a packed state array of 13 indices and splits 
        it into 4 arrays:
        position - [:3]
        velocity - [3:6]
        attitude - [6:10] (longer for quaternion)
        omega    - [10:13]
    """
    return np.split(packed, [3, 6, 10])

def motion_model(_time_delta:float, y:arr, mass: float, rotational_inertia:arr, thrust_force:arr, local_torque:arr):
    """ Return derivative of attitude -> angular velocity
        Return derivative of angular velocity -> angular acceleration
        Return derivative of position -> velocity
        Return derivative of velocity -> acceleration
        This must be a pure function, not part of a class & no references to self.state
    """
    _position, velocity, theta, omega = unpack(y)
    rotation_to_global = R.from_quat(theta)

    alpha_local = np.linalg.solve(rotational_inertia, local_torque)

    a_local = thrust_force / mass
    accel = rotation_to_global.apply(a_local)

    d_position_dt = velocity
    d_velocity_dt = accel - velocity
    d_theta_dt = quaternion_derivative(theta, omega)
    d_omega_dt = alpha_local - omega

    return pack([d_position_dt, d_velocity_dt, d_theta_dt, d_omega_dt])

class MockController(AbstractController):
    """ Mock motor controller that has same input API but which
        integrates to generate fake state based on the input
    """
    def __init__(self, log):
        log("Mock Controller: __init__()")
        self.getter_lock = Lock()
        self.setter_lock = Lock()
        self.state = InitialState(
            position = np.array([0.0, 0.0, 0.0]),
            velocity = np.array([0.0, 0.0, 0.0]),
            local_force = np.array([0.0, 0.0, 0.0]),
            attitude = np.array([0.0, 0.0, 0.0]),
            angular_velocity = np.array([0.0, 0.0, 0.0]),
            local_torque = np.array([0.0, 0.0, 0.0]),
            mass = 1.0,
            inertia = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]),
        )
        self.last_time = time()
        self.motor_speeds = MotorSpeeds(
            forward = 0,
            turn = 0,
            front = 0,
            back = 0,
        )
        self.log = log
    
    def set_speeds(self, input:MotorSpeeds, verbose=False):
        """ Replicates API of real motor controller, setting motor speeds to manipulate 
            state of system. Also records initial time to integrate against
        """
        with self.setter_lock:
            if verbose:
                self.log("Mock Controller: set_speeds()")
            # This must be called so that the previous integration is taken into account
            self.get_state()

            self.motor_speeds.forward = input.forward 
            self.motor_speeds.turn = input.turn
            self.motor_speeds.front = input.front
            self.motor_speeds.back = input.back
            
            self.state.local_force[0] = input.forward 
            self.state.local_torque[2] = input.turn
            self.state.local_force[2] = input.front * 0.5
            self.state.local_force[2] = input.back * 0.5

            self.state.local_torque[1] = 0
            self.state.local_torque[1] += input.front * 0.5
            self.state.local_torque[1] -= input.back * 0.5

            self.set_last_time()
            return

    def set_zeros(self):
        """ Sets all fake motor values to zero.
        """
        with self.setter_lock:
            self.log("Mock Controller: set_zeros()")
            self.get_state()

            self.motor_speeds.forward = 0
            self.motor_speeds.turn = 0
            self.motor_speeds.front = 0
            self.motor_speeds.back = 0

            self.state.local_force[0] = 0
            self.state.local_torque[1] = 0

            self.set_last_time()
            return

    def set_last_time(self):
        """ Call this when the state is changed by an input (changing a motor
            speed) to create a new initial time to integrate against.
        """
        self.last_time = time()

    def get_state(self) -> State:
        """ Returns the simulated state using the last known position, velocity,
            attitude, and angular velocity, as well as the known time elapsed.
        """
        with self.getter_lock:
            #log("Motor Controller: get_state()")
            time_delta = time() - self.last_time
            self.last_time = time()

            packed = pack([
                self.state.position,
                self.state.velocity,
                R.from_euler('XYZ', self.state.attitude, True).as_quat(True),
                self.state.angular_velocity
            ]);

            solution = solve_ivp(
                fun=motion_model,
                t_span=(0,time_delta),
                y0=packed,
                args=(
                    self.state.mass,
                    self.state.inertia,
                    self.state.local_force,
                    self.state.local_torque
                )
            );

            self.state.position, \
            self.state.velocity, \
            quat_attitude, \
            self.state.angular_velocity = unpack(solution.y[:,-1]);
            
            self.state.attitude = R.from_quat(quat_attitude).as_euler('XYZ', True)

            return self.state

if __name__ == "__main__":
    mock = MockController(print)
    try:
        while True:
            state = mock.get_state()
            serial_state = SerialState(
                position = state.position.tolist(),
                velocity = state.velocity.tolist(),
                attitude = state.attitude.tolist(),
                angular_velocity = state.angular_velocity.tolist(),
            )
            print(serial_state.model_dump_json(indent=2))

    except KeyboardInterrupt:
        print("Quitting")
