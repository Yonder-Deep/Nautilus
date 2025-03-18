from .motor_controller import MotorController
from custom_types import State, InitialState

from time import time
from threading import Lock
import numpy as np
from scipy.spatial.transform import Rotation as R
from scipy.integrate import solve_ivp

# Move this
def quaternion_derivative(q, omega):
    """Calculates the quaternion derivative given quaternion and angular velocity."""
    q_w, q_x, q_y, q_z = q
    return 0.5 * np.array([
        -q_x * omega[0] - q_y * omega[1] - q_z * omega[2],
        q_w * omega[0] + q_y * omega[2] - q_z * omega[1],
        q_w * omega[1] - q_x * omega[2] + q_z * omega[0],
        q_w * omega[2] + q_x * omega[1] - q_y * omega[0],
    ])

class MockController(MotorController):
    """ Mock motor controller that has same input API but which
        integrates to generate fake state based on the input
    """
    def __init__(self):
        print("MC INIT")
        self.lock = Lock() # Prevent access by multiple threads simultaneously -> `with self.lock`
        self.state = InitialState(
            position = np.array([0.0, 0.0, 0.0]),
            velocity = np.array([0.0, 0.0, 0.0]),
            local_velocity = np.array([0.0, 0.0, 0.0]),
            local_force = np.array([1.0, 0.0, 0.0]),
            attitude = np.array([1.0, 0.0, 0.0, 0.0]),
            angular_velocity = np.array([0.0, 0.0, 0.0]),
            local_torque = np.array([0.0, 0.0, 0.1]),
            mass = 1.0,
            inertia = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]),
            forward_m_input = 0.0,
            turn_m_input = 0.0
        )
        self.last_time = time()
    
    def set_speeds(self, input=tuple[float, float]):
        """ Replicates API of real motor controller, setting motor speeds to manipulate 
            state of system. Also records initial time to integrate against
        """
        with self.lock:
            print("MC SET")
            self.state.forward_m_input= input[0]
            self.state.turn_m_input = input[1]

            # This will need to be altered when drag & terminal vel is considered
            self.state.local_force[0] = input[0]
            self.state.local_torque[2] = input[1]

            self.last_time = time()

    def get_state(self):
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
            self.state.attitude = rotation.as_quat()

            acceleration = rotation.apply(a_local) # Transform from local to global frame
            self.state.velocity += acceleration * time_delta
            self.state.position += self.state.velocity * time_delta

        return self.state