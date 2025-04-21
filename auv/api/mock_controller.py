from abc import abstractmethod

if __name__ == "__main__":
    import sys
    sys.path.append("..")
from custom_types import State, InitialState, SerialState

from time import time
from threading import Lock
import numpy as np
from numpy import ndarray as arr
from numpy import float64 as f64
from scipy.spatial.transform import Rotation as R
from scipy.integrate import solve_ivp

class AbstractController():
    @abstractmethod
    def set_speeds(self, input):
        pass

    @abstractmethod
    def get_state(self) -> State:
        pass
    
    @abstractmethod
    def set_last_time(self):
        pass

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
    #alpha = rotation_to_global.apply(alpha_local)

    a_local = thrust_force / mass
    accel = rotation_to_global.apply(a_local)

    d_position_dt = velocity
    d_velocity_dt = accel
    d_theta_dt = quaternion_derivative(theta, omega)
    d_omega_dt = alpha_local

    return pack([d_position_dt, d_velocity_dt, d_theta_dt, d_omega_dt])

class MockController(AbstractController):
    """ Mock motor controller that has same input API but which
        integrates to generate fake state based on the input
    """
    def __init__(self):
        print("MC INIT")
        self.lock = Lock() # Prevent access by multiple threads simultaneously -> `with self.lock`
        self.state = InitialState(
            position = np.array([0.0, 0.0, 0.0]),
            velocity = np.array([0.0, 0.0, 0.0]),
            local_force = np.array([0.2, 0.0, 0.0]),
            attitude = np.array([0.0, 0.0, 0.0, 1.0]), # X Y Z W
            angular_velocity = np.array([0.0, 0.2, 0.0]),
            local_torque = np.array([0.0, 0.0, 0.1]),
            mass = 1.0,
            inertia = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]),
        )
        self.last_time = time()
    
    def set_speeds(self, input=tuple[float, float]):
        """ Replicates API of real motor controller, setting motor speeds to manipulate 
            state of system. Also records initial time to integrate against
        """
        with self.lock:
            print("MC SET")
            # This must be called so that the previous integration 
            # is taken into account
            self.get_state()
            forward, turn = input

            # This will need to be altered when drag & terminal vel is considered
            self.state.local_force[0] = forward
            self.state.local_torque[1] = turn

            self.set_last_time()

    def set_last_time(self):
        """ Call this when the state is changed by an input (changing a motor
            speed) to create a new initial time to integrate against.
        """
        self.last_time = time()

    def get_state(self) -> InitialState:
        """ Returns the simulated state using the last known position, velocity,
            attitude, and angular velocity, as well as the known time elapsed.
        """
        with self.lock:

            print("MC GET")
            time_delta = time() - self.last_time
            self.last_time = time()

            packed = pack([
                self.state.position,
                self.state.velocity,
                self.state.attitude,
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
            self.state.attitude, \
            self.state.angular_velocity = unpack(solution.y[:,-1]);

            return self.state

    def get_state_euler(self):
        """ Simple first order euler implementation of get_state()
        """
        with self.lock:
            print("MC GET")
            time_delta = time() - self.last_time
            self.last_time = time()

            quat = self.state.attitude / np.linalg.norm(self.state.attitude) 
            rotation = R.from_quat(quat)

            # a = F / m
            a_local = self.state.local_force / self.state.mass
            self.state.local_velocity += a_local * time_delta

            # alpha = I / tau
            alpha_local = np.linalg.solve(self.state.inertia, self.state.local_torque)  # Solve I * alpha = tau

            # omega = omega_i + alpha * ∆t
            self.state.angular_velocity += alpha_local * time_delta

            # Not sure if this will work, overloaded * while in *= form
            rotation *= R.from_rotvec(self.state.angular_velocity * time_delta)
            self.state.attitude = np.asarray(rotation.as_quat(True), dtype=f64)

            acceleration = rotation.apply(a_local) # Transform from local to global frame
            self.state.velocity += np.asarray(acceleration * time_delta, dtype=f64)
            self.state.position += self.state.velocity * time_delta

            return self.state

if __name__ == "__main__":
    mock = MockController()
    try:
        while True:
            state = mock.get_state()
            serial_state = SerialState(
                position = state.position.tolist(),
                velocity = state.velocity.tolist(),
                local_force = state.local_force.tolist(),
                attitude = state.attitude.tolist(),
                angular_velocity = state.angular_velocity.tolist(),
                local_torque = state.local_torque.tolist(),
            )
            print(serial_state.model_dump_json(indent=2))

    except KeyboardInterrupt:
        print("Quitting")
