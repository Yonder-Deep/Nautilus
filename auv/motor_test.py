from api import MotorController
import time

mc = MotorController()

mc.update_motor_speeds(
    [
        20,
        20,
        20,
        20,
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
