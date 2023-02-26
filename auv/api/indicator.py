import RPi.GPIO as GPIO
import time


class Indicator:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(14, GPIO.IN)
        GPIO.setup(12, GPIO.OUT)
        print("LED on")
        GPIO.output(12, GPIO.HIGH)
        time.sleep(10)
        print("LED off")
        GPIO.output(12, GPIO.LOW)
