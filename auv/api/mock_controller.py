from .motor_controller import MotorController
from custom_types import State
from time import time
from threading import Lock

class MockController(MotorController):
    """ Mock motor controller that has same input API but which
        integrates to generate fake state based on the input
    """
    def __init__(self):
        print("MC INIT")
        self.lock = Lock()
        self.state = State(
            global_position = [0.0, 0.0, 0.0],
            global_velocity = [0.0, 0.0, 0.0],
            local_velocity = [0.0, 0.0, 0.0],
            attitude = [0.0, 0.0, 0.0],
            angular_velocity = [0.0, 0.0, 0.0],
            forward_m_input = 0.0,
            turn_m_input = 0.0
        )
        self.last_time_get = time()
        self.last_time_set = time()
        self.last_time = time()
    
    def set_speeds(self, input=tuple[float, float]):
        with self.lock:
            print("MC SET")
            self.state.forward_m_input= input[0]
            self.turn_m_input= input[1]
            # No acceleration yet

            self.last_time_set = time()
            self.last_time = time()

    def get_state(self):
        with self.lock:
            print("MC GET")
            time_delta = time() - self.last_time
            self.last_time_get = time()

            self.state.attitude[0] = 0.5 * self.state.turn_m_input * time_delta**2
            
            # delta_x = v_i * t + 0.5at^2
            local_position_delta = self.state.local_velocity[0] * time_delta + 0.5 * self.state.forward_m_input * time_delta**2

            # v_f = v_i + delta_a * delta_t 
            self.state.local_velocity[0] += self.state.forward_m_input * time_delta
            import numpy as np

#def update_state(
#    p, v, q, F_local, tau_local, m, I, dt
#):  # All inputs as NumPy arrays
#    """Updates the object's state using Euler integration."""

            # 1. Linear Acceleration (Local)
            a_local = F_local / m

            # 2. Angular Acceleration (Local)
            alpha_local = np.linalg.solve(I, tau_local)  # Solve I * alpha = tau

            # 3. Angular Velocity
            omega = alpha_local * dt

            # 4. Quaternion Update
            q_w, q_x, q_y, q_z = q
            delta_q = (
                0.5
                * np.array(
                    [
                        -q_x * omega[0] - q_y * omega[1] - q_z * omega[2],
                        q_w * omega[0] + q_y * omega[2] - q_z * omega[1],
                        q_w * omega[1] - q_x * omega[2] + q_z * omega[0],
                        q_w * omega[2] + q_x * omega[1] - q_y * omega[0],
                    ]
                )
                * dt
            )
            q = q + delta_q
            q = q / np.linalg.norm(q)  # Normalize quaternion

            # 5. Rotation Matrix (from quaternion)
            R = np.array(
                [
                    [1 - 2 * (q_y**2 + q_z**2), 2 * (q_x * q_y - q_w * q_z), 2 * (q_x * q_z + q_w * q_y)],
                    [2 * (q_x * q_y + q_w * q_z), 1 - 2 * (q_x**2 + q_z**2), 2 * (q_y * q_z - q_w * q_x)],
                    [2 * (q_x * q_z - q_w * q_y), 2 * (q_y * q_z + q_w * q_x), 1 - 2 * (q_x**2 + q_y**2)],
                ]
            )

            # 6. Linear Acceleration (Global)
            a_global = R @ a_local

            # 7. Linear Velocity (Global)
            v = v + a_global * dt

            # 8. Position (Global)
            p = p + v * dt

        return self.state
        