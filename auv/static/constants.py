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
RADIO_PATH_9 = {
    "radioNum": 9,
    "path": "/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.3:1.0-port0",
}

RADIO_PATH_10 = {
    "radioNum": 10,
    "path": "/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.1:1.0-port0",
}
RADIO_PATH_11 = {
    "radioNum": 11,
    "path": "/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.4:1.0-port0",
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
    RADIO_PATH_9,
    RADIO_PATH_10,
    RADIO_PATH_11,
]
GPS_PATH = (
    "/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0"
)
GPS_PATH_2 = (
    "/dev/serial/by-id/usb-u-blox_AG_-_www.u-blox.com_u-blox_7_-_GPS_GNSS_Receiver-if00"
)
GPS_PATH_3 = "/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.2:1.0"
GPS_PATH_4 = "/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.3:1.0"
GPS_PATH_5 = "/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.4:1.0"
GPS_PATH_6 = "/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.1:1.0"

# encode sizes and generalizations
GPS_PATHS = [GPS_PATH, GPS_PATH_2, GPS_PATH_3, GPS_PATH_4, GPS_PATH_5, GPS_PATH_6]
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

# IMU sensor constants (kg/m^3 convenience)
DENSITY_FRESHWATER = 997
DENSITY_SALTWATER = 1029
FLUID_DENSITY = DENSITY_FRESHWATER

# Dive PID constants
P_PITCH = 0.05
I_PITCH = 0.7
D_PITCH = 0.01
P_DEPTH = 80.0
I_DEPTH = 0.1
D_DEPTH = 0.1
P_HEADING = 0.7
I_HEADING = 0.5
D_HEADING = 0.0

DEF_DIVE_SPD = 100
MAX_TIME = 600
MAX_ITERATION_COUNT = MAX_TIME / SEND_SLEEP_DELAY / 7

# AUV Sensor Data Encoding headers
HEADING_DATA = 0b10001
MISC_DATA = 0b10010
DEPTH_DATA = 0b10011
POSITION_DATA = 0b10100
FILE_DATA = 0b10101

# BS Command Encoding headers
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
TEST_HEADING_COMMAND = 0b01111

DEPTH_ENCODE = DEPTH_DATA << HEADER_SHIFT
HEADING_ENCODE = HEADING_DATA << HEADER_SHIFT
MISC_ENCODE = MISC_DATA << HEADER_SHIFT
POSITION_ENCODE = POSITION_DATA << HEADER_SHIFT
PID_ENCODE = PID_COMMAND << HEADER_SHIFT
NAV_ENCODE = NAV_COMMAND << HEADER_SHIFT  # | with XSY (forward, angle sign, angle)
MOTOR_TEST_ENCODE = MOTOR_TEST_COMMAND << HEADER_SHIFT
XBOX_ENCODE = XBOX_COMMAND << HEADER_SHIFT  # | with XY (left/right, down/up xbox input)
MISSION_ENCODE = MISSION_COMMAND << HEADER_SHIFT  # | with X   (mission)
DIVE_ENCODE = DIVE_COMMAND << HEADER_SHIFT  # | with D   (depth)
KILL_ENCODE = KILL_COMMAND << HEADER_SHIFT  # | with X (kill all / restart threads)
MANUAL_DIVE_ENCODE = MANUAL_DIVE_COMMAND << HEADER_SHIFT

LOCK = threading.Lock()  # checks if connected to BS over radio
RADIO_LOCK = threading.Lock()  # ensures one write to radio at a time

FILE_SEND_PACKET_SIZE = PAYLOAD_BUFFER_WIDTH  # bytes
DIVE_LOG = "dive_log.txt"


def log(val):
    print("[AUV]\t" + val)
