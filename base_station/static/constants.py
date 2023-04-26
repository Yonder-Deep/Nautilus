import threading

# Constants for the base station
THREAD_SLEEP_DELAY = 0.2  # Since we are the slave to AUV, we must run faster.
PING_SLEEP_DELAY = 3
RADIO_PATH = {'radioNum': 1, 'path': '/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0'}
RADIO_PATH_2 = {'radioNum': 2, 'path': '/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_D30AEU3V-if00-port0'}
RADIO_PATH_3 = {'radioNum': 3, 'path': '/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_D30AFD0I-if00-port0'}
RADIO_PATH_4 = {'radioNum': 4, 'path': '/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_D30AFALT-if00-port0'}
RADIO_PATH_5 = {'radioNum': 5, 'path': '/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_D30AF7PZ-if00-port0'}
RADIO_PATH_6 = {'radioNum': 6, 'path': 'COM5'}
RADIO_PATH_7 = {'radioNum': 7, 'path': 'COM4'}
RADIO_PATH_8 = {'radioNum': 8, 'path': 'COM7'}
RADIO_PATH_9 = {'radioNum': 9, 'path': 'COM8'}
RADIO_PATH_10 = {'radioNum': 10, 'path': '/dev/serial/by-id/usb-FTDI_FT231X_USB_UART_D30EZV09-if00-port0'}
RADIO_PATH_11 = {'radioNum': 11, 'path': 'COM9'}
RADIO_PATH_12 = {'radioNum': 12, 'path': 'COM10'}
RADIO_PATHS = [RADIO_PATH, RADIO_PATH_2, RADIO_PATH_3, RADIO_PATH_4, RADIO_PATH_5,
               RADIO_PATH_6, RADIO_PATH_7, RADIO_PATH_8, RADIO_PATH_9, RADIO_PATH_10, RADIO_PATH_11, RADIO_PATH_12]
GPS_PATH = '/dev/serial/by-id/usb-u-blox_AG_-_www.u-blox.com_u-blox_7_-_GPS_GNSS_Receiver-if00'
PING = 0xFFFFFFFFFFFFFF

CONNECTION_TIMEOUT = 6  # Seconds before BS is determined to have lost radio connection to AUV

# AUV Constants (these are also in auv.py)
MAX_AUV_SPEED = 100
MAX_TURN_SPEED = 50

# Encoding headers
FILE_DATA = 0b101

FILE_ENCODE = FILE_DATA << 21

FILE_DL_PACKET_SIZE = 7  # Number to be determined (bytes)

lock = threading.Lock()  # lock for writing to out_q to GUI
radio_lock = threading.Lock()   # lock for writing to radio

# Heat Regulation in Pi
SAFE_TEMP = 60
HOT_TEMP = 80
