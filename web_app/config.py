import threading

# Constants for the base station connections
THREAD_SLEEP_DELAY = 0.2  # Since we are the slave to AUV, we must run faster.
PING_SLEEP_DELAY = 3

AUV_IP_ADDRESS = 'ws://192.168.100.11'
AUV_PING_INTERVAL = 6

radio_lock = threading.Lock()  # lock for writing to radio

RADIO_PATH_1 = {"radioNum": 1, "path":"/dev/serial/tty*"}
RADIO_PATHS = [ RADIO_PATH_1 ]

# Heat Regulation in Pi
SAFE_TEMP = 60
HOT_TEMP = 80
