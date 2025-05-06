"""
The motor class calibrates and sets the speed of an individual motor.
"""
import time
import pigpio

CENTER_PWM_RANGE = 400
CENTER_PWM_VALUE = 1500
MAX_SPEED = 150


class Motor:
    def __init__(self, gpio_pin, pi):
        """
        Instantiate a motor.

        gpio_pin: Pin on Raspberry Pi that this motor is connected to.i
        pi:       Raspberry Pi GPIO object
        """
        self.pin = gpio_pin
        self.pi = pi
        self.speed = 0

    def arm_motor(self): 
        """
        Arms the ESC by sending a minimum throttle signal for a few seconds.
        """
        print(f"Arming motor on GPIO {self.pin}...")
        self.pi.set_servo_pulsewidth(self.pin, 1000)  # Send 1000 µs (min throttle)
        time.sleep(3)
        self.pi.set_servo_pulsewidth(self.pin, 0)     # Optional: stop signal
        print("ESC should now be armed.")

    def set_speed(self, speed):
        """
        Sets the speed of the motor.

        speed: double value specifying the speed that the motor should be set to.
        """

        self.speed = speed

        # Threshold for positive or negative speed.
        if speed > MAX_SPEED:
            speed -= MAX_SPEED
            speed *= -1

        # Conversion from received radio speed to PWM value.
        pwm_speed = speed * (CENTER_PWM_RANGE) / MAX_SPEED + CENTER_PWM_VALUE

        # Change speed of motor.
        self.pi.set_servo_pulsewidth(self.pin, pwm_speed)

    def test_motor(self):
        """
        Test the motor by setting speed values between time intervals.
        """
        print(f"TESTING MOTOR (GPIO = {self.pin})")
        self.set_speed(MAX_SPEED / 3)
        time.sleep(5)
        self.set_speed(0)


if __name__ == "__main__":
    pi = pigpio.pi()
    while True:
        for i in range(0, 25):
            try:
                motor = Motor(i, pi)
                #print("Testing Motor: {}".format(str(i)))
                motor.test_motor()
            except:
                print("Skipped: {}".format(str(i)))
