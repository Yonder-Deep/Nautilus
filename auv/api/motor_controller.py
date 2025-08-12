import pigpio
import time
import sys

try:
    from .motor import Motor
    from .abstract import AbstractController
    from models.data_types import MotorSpeeds
except ImportError: # When running standalone, import differently
    import sys
    sys.path.append("..")
    from motor import Motor
    from abstract import AbstractController
    from models.data_types import MotorSpeeds

# Indices for motor array [WHEN REMAPPING, CHANGE THESE AND NOT GPIOS]
FORWARD_MOTOR_INDEX = 0         # in the back
TURN_MOTOR_INDEX = 3            # in the front
FRONT_MOTOR_INDEX = 1           # goes up/down
BACK_MOTOR_INDEX = 2            # goes up/down

# GPIO Pin numbers for Motors
FORWARD_GPIO_PIN = 4
TURN_GPIO_PIN = 11
FRONT_GPIO_PIN = 18
BACK_GPIO_PIN = 24

# Define pin numbers for PI (the number of the pins when counting them physically, different because some Pi pins are not GPIO pins)
FORWARD_PI_PIN = 7          # Left pins
TURN_PI_PIN = 23            # Right pins
FRONT_PI_PIN = 12           # Back pins
BACK_PI_PIN = 18            # Front pins

# Constants
BALLAST = 4
MAX_PITCH = 30
MAX_CORRECTION_MOTOR_SPEED = 25  # Max turning speed during pid correction

class MotorController(AbstractController):
    """ Object that manages and abstracts all interactions with the motor array
        for the AUV
    """

    def __init__(self, log):
        """
        Initializes MotorController object and individual motor objects
        to respective gpio pins.
        """
        # Connection to Raspberry Pi GPIO ports.
        self.pi = pigpio.pi()

        # Motor object definitions.
        self.motor_pins = [FORWARD_GPIO_PIN, TURN_GPIO_PIN,
                           FRONT_GPIO_PIN, BACK_GPIO_PIN]

        self.pi_pins = [FORWARD_PI_PIN, TURN_PI_PIN, FRONT_PI_PIN, BACK_PI_PIN]

        self.motors = [Motor(gpio_pin=pin, pi=self.pi)
                       for pin in self.motor_pins]

        self.forward_speed = 0
        self.turn_speed = 0
        self.front_speed = 0
        self.back_speed = 0
        self.log = log

    def set_speeds(self, input:MotorSpeeds, verbose=False) -> None:
        """
        Sets motor speeds to each individual motor. This is for manual (xbox) control when the
        radio sends a data packet of size 4.

        data: String read from the serial connection containing motor speed values.
        """
        # Parse motor speed from data object.
        self.forward_speed = input.forward * 255
        self.turn_speed = input.turn * 255
        self.front_speed = input.front * 255
        self.back_speed = input.back * 255

        # Set motor speed
        self.motors[FORWARD_MOTOR_INDEX].set_speed(self.forward_speed)
        print("Forward motor speed: ", self.forward_speed)
        self.motors[TURN_MOTOR_INDEX].set_speed(self.turn_speed)
        print("Turning motor speed: ", self.turn_speed)
        self.motors[FRONT_MOTOR_INDEX].set_speed(self.front_speed)
        print("Dive (front) motor speed: ", self.front_speed)
        self.motors[BACK_MOTOR_INDEX].set_speed(self.back_speed)
        print("Dive (back) motor speed: ", self.back_speed)

    def pid_motor(self, pid_feedback):
        """
        Updates the TURN motor based on the PID feedback. 

        feedback: Feedback value from pid class.
        """
        if (not pid_feedback):
            self.turn_speed = 0
        else:
            self.turn_speed = self.calculate_pid_new_speed(pid_feedback)

#        log('[PID_MOTOR] %7.2f %7.2f' %
 #             (self.left_speed, self.right_speed), end='\n')

        self.motors[TURN_MOTOR_INDEX].set_speed(self.turn_speed)

    def pid_motor_pitch(self, pid_feedback, current_value):
        """
        Updates front and back  motor speed based off pid feedback

        feedback: Feedback value from pid class.
        """
        if (not pid_feedback):
            self.front_speed = 0
            self.back_speed = 0
        elif abs(current_value) > 30:
            # double the motor speed for the motor in the water
            double_motor_speed = pid_feedback * 2
            if current_value > MAX_PITCH:
                # Front motor is out of water, set speed to 0 to prevent breaking
               # When not flipped: vvvv
                self.front_speed = 0
                self.back_speed = self.calculate_pid_new_speed(
                    -double_motor_speed)
               # WHen flipped: vvvv
               # self.front_speed = self.calculate_pid_new_speed(double_motor_speed)
               # self.back_speed = 0
            else:
                # Back motor is out of water, set speed to 0 for front motor
                # WHen not flipped: vvvv
                self.front_speed = self.calculate_pid_new_speed(
                    double_motor_speed)
                self.back_speed = 0
                # WHen flipped: vvv
                #self.front_speed = 0
                #self.back_speed = self.calculate_pid_new_speed(-double_motor_speed)
        else:

            # When not flipped, use +
            self.front_speed = self.calculate_pid_new_speed(+pid_feedback)
            # When not flipped, use -
            self.back_speed = self.calculate_pid_new_speed(-pid_feedback)

      #  log('[PID_MOTOR] %7.2f %7.2f' %
     #         (self.front_speed, self.back_speed), end='\n')
        self.motors[FRONT_MOTOR_INDEX].set_speed(self.front_speed)
        self.motors[BACK_MOTOR_INDEX].set_speed(self.back_speed)

    def set_zeros(self):
        """
        Sets motor speeds of each individual motor to 0.
        """
        for motor in self.motors:
            motor.set_speed(0)

        self.log("motors set to [0, 0, 0, 0]")

    def test_all(self):
        """
        Calibrates each individual motor.
        """
        self.log("Testing all motors...")
        for motor in self.motors:
            motor.test_motor()
            time.sleep(1)

    def test_forward(self):  
        self.log("Testing forward motor...")
        self.motors[FORWARD_MOTOR_INDEX].test_motor()

    def test_turn(self): 
        self.log("Testing turn motor...")
        self.motors[TURN_MOTOR_INDEX].test_motor()

    def test_front(self):
        self.log("Testing front motor...")
        self.motors[FRONT_MOTOR_INDEX].test_motor()

    def test_back(self):
        self.log("Testing back motor...")
        self.motors[BACK_MOTOR_INDEX].test_motor()

    def calculate_pid_new_speed(self, feedback):
        # Case 1: Going backward
        if (feedback < 0):
            return min(100 + abs(feedback), 100 + MAX_CORRECTION_MOTOR_SPEED)
        # Case 2: Going forward
        else:
            return min(feedback, MAX_CORRECTION_MOTOR_SPEED)

    def is_stopped(self):
        """ Returns if any of the motors are not set to zero. """
        # do not use
        return all([motor.speed == 0 for motor in self.motors])


def main():
    mc = MotorController(lambda msg: print("MC: " + msg))
    mc.test_all()


if __name__ == "__main__":
    main()
    # def calculate_pid_new_speed(self, last_speed, speed_change):
    #     #log(">>Last speed\t" + str(last_speed) + "speed_change\t" + str(speed_change))
    #     #new_speed = last_speed + speed_change
    #     # Case 1: was going forward
    #     assert(not (MAX_CORRECTION_MOTOR_SPEED < last_speed and last_speed <= 100)), "Unexpected last speed" + str(last_speed)
    #     assert(not (100 + MAX_CORRECTION_MOTOR_SPEED < last_speed and last_speed <= 200)), "Unexpected last speed" + str(last_speed)
    #     if(last_speed <= MAX_CORRECTION_MOTOR_SPEED):
    #         new_speed = last_speed + speed_change
    #         lower_speed_cap = 0
    #         upper_speed_cap = MAX_CORRECTION_MOTOR_SPEED
    #     # Case 2: was going backward
    #     else:
    #         new_speed = last_speed - speed_change
    #         lower_speed_cap = 100
    #         upper_speed_cap = 100 + MAX_CORRECTION_MOTOR_SPEED
    #
    #
    #     # Exceed speed range, too big
    #     if(new_speed > upper_speed_cap):
    #         new_speed = upper_speed_cap
    #     # Exceed, too small
    #     if(new_speed < lower_speed_cap):
    #
    #         # Was going forward, want to backward
    #         if(last_speed <= MAX_CORRECTION_MOTOR_SPEED):
    #             #log("Adjust case forward -> backward")
    #             new_speed = abs(new_speed) + 100
    #             # if it goes backward too fast
    #             if(new_speed > 100 + MAX_CORRECTION_MOTOR_SPEED):
    #                 new_speed = 100 + MAX_CORRECTION_MOTOR_SPEED
    #         else: # was going backward, want to forward
    #             #log("Adjust case backward -> forward")
    #             new_speed = 100 - new_speed
    #             # if it goes forward too fast
    #             if(new_speed > MAX_CORRECTION_MOTOR_SPEED):
    #                 new_speed = MAX_CORRECTION_MOTOR_SPEED
    #
    #     assert(not (MAX_CORRECTION_MOTOR_SPEED < new_speed and new_speed <= 100)), "Unexpected new speed output" + str(new_speed)
    #     assert(not (100 + MAX_CORRECTION_MOTOR_SPEED < new_speed and new_speed <= 200)), "Unexpected new speed output" + str(new_speed)
    #     return new_speed
