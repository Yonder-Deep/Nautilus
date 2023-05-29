import threading

# Constants for the AUV
RADIO_PATH = {
    "radioNum": 1,
    "path": "/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0",
}
RADIO_PATH_2 = {
    "radioNum": 2,
    "path": "/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_D30AEU3V-if00-port0",
}
RADIO_PATH_3 = {
    "radioNum": 3,
    "path": "/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_D30AFD0I-if00-port0",
}
RADIO_PATH_4 = {
    "radioNum": 4,
    "path": "/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_D30AFALT-if00-port0",
}
RADIO_PATH_5 = {
    "radioNum": 5,
    "path": "/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_D30AF7PZ-if00-port0",
}
RADIO_PATH_6 = {
    "radioNum": 6,
    "path": "/dev/serial/by-id/usb-FTDI_FT231X_USB_UART_D30EZO92-if00-port0",
}
RADIO_PATH_7 = {
    "radioNum": 7,
    "path": "/dev/serial/by-id/usb-FTDI_FT231X_USB_UART_D30EZV09-if00-port0",
}
RADIO_PATH_8 = {
    "radioNum": 8,
    "path": "/dev/serial/by-id/usb-FTDI_FT231X_USB_UART_D30AF7PZ-if00-port0",
}
RADIO_PATHS = [
    RADIO_PATH,
    RADIO_PATH_2,
    RADIO_PATH_3,
    RADIO_PATH_4,
    RADIO_PATH_5,
    RADIO_PATH_6,
    RADIO_PATH_7,
    RADIO_PATH_8,
]
GPS_PATH = (
    "/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0"
)
GPS_PATH_2 = (
    "/dev/serial/by-id/usb-u-blox_AG_-_www.u-blox.com_u-blox_7_-_GPS_GNSS_Receiver-if00"
)

# encode sizes and generalizations
GPS_PATHS = [GPS_PATH, GPS_PATH_2]
IMU_PATH = "/dev/serial0"
IMU_RESET_PIN = 8
PAYLOAD_BUFFER_WIDTH = 8  # the length in bytes of a single bytestring used to communicate over radio, change as needed
HEADER_SIZE = 5
COMM_BUFFER_WIDTH = PAYLOAD_BUFFER_WIDTH + 4  # 4 is the length of the crc32
HEADER_SHIFT = PAYLOAD_BUFFER_WIDTH * 8 - HEADER_SIZE
PING = int("0x" + "F" * 2 * PAYLOAD_BUFFER_WIDTH, 16)
SEND_SLEEP_DELAY = 1
RECEIVE_SLEEP_DELAY = 0.2
PING_SLEEP_DELAY = 3
CONNECTION_TIMEOUT = 6

# Dive PID constants
P_PITCH = 5.0
I_PITCH = 2.0
D_PITCH = 0.0
P_DEPTH = 10.0
I_DEPTH = 2.0
D_DEPTH = 0.0
P_HEADING = 5.0
I_HEADING = 2.0
D_HEADING = 0.0

DEF_DIVE_SPD = 100
MAX_TIME = 600
MAX_ITERATION_COUNT = MAX_TIME / SEND_SLEEP_DELAY / 7

'''
# Encoding headers
POSITION_DATA = 0b000
HEADING_DATA = 0b001
MISC_DATA = 0b010
TEMP_DATA = 0b10011
DEPTH_DATA = 0b011
PID_DATA = 0b010
NAV_DATA = 0b100
MOTOR_TEST_DATA = 0b101
XBOX_DATA = 0b111
MISSION_DATA = 0b000
DIVE_DATA = 0b110
KILL_DATA = 0b001
MANUAL_DIVE_DATA = 0b011

DEPTH_ENCODE = DEPTH_DATA << (PAYLOAD_BUFFER_WIDTH * 8 - 3)
HEADING_ENCODE = HEADING_DATA << (PAYLOAD_BUFFER_WIDTH * 8 - 3)
MISC_ENCODE = MISC_DATA << (PAYLOAD_BUFFER_WIDTH * 8 - 3)
POSITION_ENCODE = POSITION_DATA << (PAYLOAD_BUFFER_WIDTH * 8 - 3)
PID_ENCODE = PID_DATA << (PAYLOAD_BUFFER_WIDTH * 8 - 3)
# changed all of these from 21 to 53 to comply to new standard bcuz of gps data
# Header encodings from BS
# NAV_ENCODE = 0b100000000000000000000000  # | with XSY (forward, angle sign, angle)
NAV_ENCODE = NAV_DATA << HEADER_SHIFT  # | with XSY (forward, angle sign, angle)
# MOTOR_TEST_ENCODE = 0b101000000000000000000000
MOTOR_TEST_ENCODE = MOTOR_TEST_DATA << HEADER_SHIFT
# XBOX_ENCODE = 0b111000000000000000000000  # | with XY (left/right, down/up xbox input)
XBOX_ENCODE = XBOX_DATA << HEADER_SHIFT  # | with XY (left/right, down/up xbox input)
# MISSION_ENCODE = 0b000000000000000000000000  # | with X   (mission)
MISSION_ENCODE = MISSION_DATA << HEADER_SHIFT  # | with X   (mission)
# DIVE_ENCODE = 0b110000000000000000000000  # | with D   (depth)
DIVE_ENCODE = DIVE_DATA << HEADER_SHIFT  # | with D   (depth)
# KILL_ENCODE = 0b001000000000000000000000  # | with X (kill all / restart threads)
KILL_ENCODE = KILL_DATA << HEADER_SHIFT  # | with X (kill all / restart threads)
# MANUAL_DIVE_ENCODE = 0b011000000000000000000000
MANUAL_DIVE_ENCODE = MANUAL_DIVE_DATA << HEADER_SHIFT
'''


LOCK = threading.Lock()  # checks if connected to BS over radio
RADIO_LOCK = threading.Lock()  # ensures one write to radio at a time

FILE_SEND_PACKET_SIZE = PAYLOAD_BUFFER_WIDTH  # bytes
DIVE_LOG = "dive_log.txt"


def log(val):
    print("[AUV]\t" + val)
