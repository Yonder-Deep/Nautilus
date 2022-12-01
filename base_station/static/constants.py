import threading
import os

# Constants for the base station
THREAD_SLEEP_DELAY = 0.2  # Since we are the slave to AUV, we must run faster.
PING_SLEEP_DELAY = 3
RADIO_PATH = {'radioNum': 1, 'path': '/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0'}
RADIO_PATH_2 = {'radioNum': 2, 'path': '/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_D30AEU3V-if00-port0'}
RADIO_PATH_3 = {'radioNum': 3, 'path': '/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_D30AFD0I-if00-port0'}
RADIO_PATH_4 = {'radioNum': 4, 'path': '/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_D30AFALT-if00-port0'}
RADIO_PATH_5 = {'radioNum': 5, 'path': '/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_D30AF7PZ-if00-port0'}
RADIO_PATHS = [RADIO_PATH, RADIO_PATH_2, RADIO_PATH_3, RADIO_PATH_4, RADIO_PATH_5]
GPS_PATH = 'usb-u-blox_AG_-_www.u-blox.com_u-blox_7_-_GPS_GNSS_Receiver-if00'
PING = 0xFFFFFF

CONNECTION_TIMEOUT = 6  # Seconds before BS is determined to have lost radio connection to AUV

# AUV Constants (these are also in auv.py)
MAX_AUV_SPEED = 100
MAX_TURN_SPEED = 50

# Encoding headers
FILE_DATA = 0b101

FILE_ENCODE = FILE_DATA << 21

FILE_DL_PACKET_SIZE = 50  # Number to be determined (bytes)

LOG_FOLDER_PATH = os.path.dirname(os.path.dirname(__file__)) + "/logs/"
AUDIO_FOLDER_PATH = os.path.dirname(os.path.dirname(__file__)) + "/hydrophone_audio/"

lock = threading.Lock()  # lock for writing to out_q to GUI
radio_lock = threading.Lock()   # lock for writing to radio

# Heat Regulation in Pi
SAFE_TEMP = 60
HOT_TEMP = 80
