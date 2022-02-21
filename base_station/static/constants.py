import threading

# Constants for the base station
THREAD_SLEEP_DELAY = 0.2  # Since we are the slave to AUV, we must run faster.
PING_SLEEP_DELAY = 3
RADIO_PATH = '/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0'

PING = 0xFFFFFF

CONNECTION_TIMEOUT = 6  # Seconds before BS is determined to have lost radio connection to AUV

# AUV Constants (these are also in auv.py)
MAX_AUV_SPEED = 100
MAX_TURN_SPEED = 50

lock = threading.Lock()  # lock for writing to out_q to GUI
radio_lock = threading.Lock()   # lock for writing to radio

# Heat Regulation in Pi
SAFE_TEMP = 60
HOT_TEMP = 80
