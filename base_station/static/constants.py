import threading

# Constants for the base station connections
THREAD_SLEEP_DELAY = 0.2  # Since we are the slave to AUV, we must run faster.
PING_SLEEP_DELAY = 3
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
# RADIO_PATH_6 = {"radioNum": 6, "path": "COM5"}
# RADIO_PATH_7 = {"radioNum": 7, "path": "COM4"}
RADIO_PATH_8 = {"radioNum": 8, "path": "COM7"}
RADIO_PATH_9 = {"radioNum": 9, "path": "COM8"}
RADIO_PATH_10 = {
    "radioNum": 10,
    "path": "/dev/serial/by-id/usb-FTDI_FT231X_USB_UART_D30EZV09-if00-port0",
}
RADIO_PATH_11 = {"radioNum": 11, "path": "COM9"}
# RADIO_PATH_12 = {"radioNum": 12, "path": "COM10"}
RADIO_PATH_13 = {"radioNum": 13, "path": "COM12"}
RADIO_PATH_14 = {"radioNum": 14, "path": "COM13"}
RADIO_PATH_15 = {"radioNum": 15, "path": "COM14"}
RADIO_PATH_16 = {"radioNum": 16, "path": "COM20"}
RADIO_PATH_17 = {"radioNum": 17, "path": "COM15"}
RADIO_PATHS = [
    RADIO_PATH,
    RADIO_PATH_2,
    RADIO_PATH_3,
    RADIO_PATH_4,
    RADIO_PATH_5,
    # RADIO_PATH_6,
    RADIO_PATH_8,
    RADIO_PATH_9,
    RADIO_PATH_10,
    RADIO_PATH_11,
    # RADIO_PATH_12,
    RADIO_PATH_13,
    RADIO_PATH_14,
    RADIO_PATH_15,
    RADIO_PATH_16,
    RADIO_PATH_17
]
GPS_PATH = (
    "/dev/serial/by-id/usb-u-blox_AG_-_www.u-blox.com_u-blox_7_-_GPS_GNSS_Receiver-if00"
)

# Communication constants
PAYLOAD_BUFFER_WIDTH = 8  # the length of the bytes of a single line of data transmitted over radio, change as needed
HEADER_SIZE = 5
COMM_BUFFER_WIDTH = (
    PAYLOAD_BUFFER_WIDTH + 4
)  # the length of a single bytestring transmitted over radio that includes the data bytes + 4 for CRC
FILE_DL_PACKET_SIZE = PAYLOAD_BUFFER_WIDTH  # Number to be determined (bytes)
HEADER_SHIFT = PAYLOAD_BUFFER_WIDTH * 8 - HEADER_SIZE
PING = int(
    "0x" + "F" * 2 * PAYLOAD_BUFFER_WIDTH, 16
)  # a string of all 1s, length is determined by payload size --> represents a PING
INTERPRETER_TRUNC = int("0x" + "F" * 2 * PAYLOAD_BUFFER_WIDTH, 16) >> 3
CONNECTION_TIMEOUT = (
    6  # Seconds before BS is determined to have lost radio connection to AUV
)

lock = threading.Lock()  # lock for writing to out_q to GUI
radio_lock = threading.Lock()  # lock for writing to radio

# AUV Data Encoding headers
HEADING_DATA = 0b10001
MISC_DATA = 0b10010
DEPTH_DATA = 0b10011
POSITION_DATA = 0b10100
FILE_DATA = 0b10101
CALIBRATION_DATA = 0b10110

# Base Station Command Data Encoding headers
MOTOR_TEST_COMMAND = 0b00001
HALT_COMMAND = 0b00010
XBOX_COMMAND = 0b00011
KILL_COMMAND = 0b00100
MANUAL_DIVE_COMMAND = 0b00101
DIVE_COMMAND = 0b00110
CAL_DEPTH_COMMAND = 0b00111
CAL_HEADING_COMMAND = 0b01000
PID_COMMAND = 0b01001
NAV_COMMAND = 0b01010
MISSION_COMMAND = 0b01011
ABORT_COMMAND = 0b01100
DL_DATA_COMMAND = 0b01101
GET_VIDEO_COMMAND = 0b01110

# Added 2024
TEST_HEADING_COMMAND = 0b01111
TEST_IMU_CALIBRATION = 0b11001

# AUV Constants (these are also in auv.py)
MAX_AUV_SPEED = 100
MAX_TURN_SPEED = 50

# Heat Regulation in Pi
SAFE_TEMP = 60
HOT_TEMP = 80
