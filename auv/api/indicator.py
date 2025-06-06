import pigpio
import time
import platform

class Indicator:
    def __init__(self):
        print("Flashing indicator light")
        pi = pigpio.pi()
        pi.set_mode(12, pi.OUTPUT)
        print("LED on")
        pi.output(12, 1)
        time.sleep(10)
        print("LED off")
        pi.output(12, 0)
        pi.stop()
