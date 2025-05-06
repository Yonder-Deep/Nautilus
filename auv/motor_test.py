from api import MotorController
import time

def motor_test(mc=MotorController):
    """
    Blocking test that runs motors for 5 seconds each
    """

    mc.update_motor_speeds(
        [
            0,
            50,
            0,
            0,
        ]
    )
    time.sleep(5)
    mc.update_motor_speeds(
        [
            0,
            0,
            50,
            50,
        ]
    )
    time.sleep(5)
    mc.update_motor_speeds(
        [
            0,
            0,
            0,
            0,
        ]
    )

motor_test()