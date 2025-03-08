from .motor_controller import MotorController
from custom_types import State
from time import clock_settime, clock_gettime

class MockController(MotorController):
    """ Mock motor controller that has same input API but which
        integrates to generate fake state based on the input
    """
    def __init__(self):
        self.state = State(
            global_position = [0, 0, 0],
            global_velocity = [0, 0, 0],
            local_velocity = [0, 0, 0],
            attitude = [0, 0, 0],
            angular_velocity = [0, 0, 0],
            forward_m_input = 0,
            turn_m_input = 0
        )
        self.origin_time = clock_settime(0, 0)
        self.last_time = clock_gettime(0)
    
    def set_speeds(self, input=tuple[float, float]):
        self.forward_m_input= input[0]
        self.turn_m_input= input[1]
        # No acceleration yet

        self.last_time = clock_gettime(0)

    def get_state(self):
        time_delta = clock_gettime(0) - self.last_time
        self.last_time = clock_gettime(0)

        self.state.attitude[0] = self.turn_mspeed * time_delta

        # delta_x = v_i * t + 0.5at^2
        local_position_delta = self.state.local_velocity[0] * time_delta + \
                                0.5 * self.forward_m_input * time_delta^2

        # v_f = v_i + delta_a * delta_t 
        self.state.local_velocity[0] += self.forward_m_input * time_delta