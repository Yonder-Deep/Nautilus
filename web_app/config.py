import threading

# Constants for the base station connections
THREAD_SLEEP_DELAY = 0.2  # Since we are the slave to AUV, we must run faster.
PING_SLEEP_DELAY = 3

CONNECTION_TIMEOUT = (
    6  # Seconds before BS is determined to have lost radio connection to AUV
)

radio_lock = threading.Lock()  # lock for writing to radio

RADIO_PATH_1 = {"radioNum": 1, "path":"/dev/serial/tty*"}
RADIO_PATHS = [ RADIO_PATH_1 ]

# Heat Regulation in Pi
SAFE_TEMP = 60
HOT_TEMP = 80
