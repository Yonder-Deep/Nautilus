import logging
import sys
import time

from Adafruit_Python_BNO055 import BNO055

bno = BNO055.BNO055(serial_port="/dev/serial0", rst=18)

if len(sys.argv) == 2 and sys.argv[1].lower() == '-v':
    logging.basicConfig(level=logging.DEBUG)

if not bno.begin():
    raise RuntimeError("Falied to initialize BNO055! Is the sensor connected?")

status, self_test, error = bno.get_system_status()
