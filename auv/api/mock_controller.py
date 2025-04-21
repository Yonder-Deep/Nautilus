from abc import abstractmethod
from custom_types import State, InitialState

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

def quaternion_derivative(q, omega):
    """Calculates the quaternion derivative given quaternion and angular velocity."""
    q_w, q_x, q_y, q_z = q
    return 0.5 * np.array([
        -q_x * omega[0] - q_y * omega[1] - q_z * omega[2],
        q_w * omega[0] + q_y * omega[2] - q_z * omega[1],
        q_w * omega[1] - q_x * omega[2] + q_z * omega[0],
        q_w * omega[2] + q_x * omega[1] - q_y * omega[0],
    ])

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

def motion_model(_time_delta:float, y:arr, mass: float, rotational_inertia:arr, thrust_force, local_torque):
    """ Return derivative of attitude -> angular velocity
        Return derivative of angular velocity -> angular acceleration
        Return derivative of position -> velocity
        Return derivative of velocity -> acceleration
        This must be a pure function, not part of a class & no references to self.state
    """
    _position, velocity, theta, omega = unpack(y)
    rotation = R.from_quat(theta)

    alpha_local = np.linalg.solve(rotational_inertia, local_torque)
    alpha = rotation.apply(alpha_local)

    d_theta_dt = quaternion_derivative(theta, omega)

    a_local = thrust_force / mass

    accel = rotation.apply(a_local)
    vel = rotation.apply(velocity)

    d_position_dt = vel
    d_velocity_dt = accel
    d_omega_dt = alpha

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
            velocity = np.array([2.0, 0.0, 0.0]),
            local_force = np.array([-0.1, 0.0, 0.0]),
            attitude = np.array([0.0, 0.0, 0.383, 0.924]), # X Y Z W
            angular_velocity = np.array([0.0, 0.0, 0.0]),
            local_torque = np.array([0.0, 0.0, 0.0]),
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
    
