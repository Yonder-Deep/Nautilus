# File no longer used


# System imports
import serial
import time
import struct
import math
import os


class NavController:
    """ Class that converts Xbox360 input to motor speed data """

    def __init__(self, joy, max_speed=100, max_turn_speed=50):
        self.joy = joy
        self.maxSpeed = max_speed
        self.maxTurnSpeed = max_turn_speed
        self.motor_data = [0, 0, 0, 0]

    def get_data(self):
        """ Returns the motor speed data """
        return self.motor_data

    def set_data(self, forward_speed, turn_speed, front_speed, back_speed):
        """ Sets the values in stored in the current motor_data array """
        self.motor_data = [forward_speed, turn_speed, front_speed, back_speed]

    def handle(self):
        """ Converts xbox360 input into motor speed values """
    # forward_drive = self.joy.rightTrigger()  # Right trigger speed
    # backward_drive = self.joy.leftTrigger()  # Left trigger speed
    # ballast = self.joy.B()

        # Grab our xbox values
        leftStickValue = self.joy.leftX()
        rightTriggerVal = self.joy.rightTrigger()
        leftTriggerVal = self.joy.leftTrigger()

        # Set turn speed
        motorSpeedTurn = int(self.maxTurnSpeed * leftStickValue)

        # Set forward speed, prioritizing forward motion.
        motorSpeedForward = 0
        if rightTriggerVal > 0:
            motorSpeedForward = int(rightTriggerVal*self.maxSpeed)
        elif leftTriggerVal > 0:
            motorSpeedForward = int(-1*leftTriggerVal*self.maxSpeed)

        # Set motor speed values
        self.set_data(motorSpeedForward, motorSpeedTurn, 0, 0)
    # Left, right, down, up controls
    # elif forward_drive or backward_drive:
    #     if forward_drive:
    #         motorSpeedBase = int(forward_drive*self.maxSpeed)
    #     elif backward_drive:
    #         motorSpeedBase = int(-1*backward_drive * self.maxSpeed)

    #     # Don't change; Raman's magic code
    #     leftStickValue = math.floor(
    #         ((self.joy.leftX() + 1) / 2) * self.motorIncrements) / self.motorIncrements
    #     motorSpeedLeft = int(leftStickValue * motorSpeedBase)
    #     motorSpeedRight = int((1 - leftStickValue) * motorSpeedBase)

    #     if motorSpeedLeft < 0:
    #         motorSpeedLeft *= -1
    #         motorSpeedLeft += 100

    #     if motorSpeedRight < 0:
    #         motorSpeedRight *= -1
    #         motorSpeedRight += 100

    #     if self.debug:
    #         print("Left motor ", str(motorSpeedLeft))
    #         print("Right motor ", str(motorSpeedRight))

    #     self.cb['MAN'](motorSpeedLeft, motorSpeedRight, 0, 0)

    # elif ballast:
    #     self.cb['BAL']()
