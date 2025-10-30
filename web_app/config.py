import threading

# Constants for the base station connections
THREAD_SLEEP_DELAY = 0.2  # Since we are the slave to AUV, we must run faster.
PING_SLEEP_DELAY = 3

AUV_IP_ADDRESS = 'ws://localhost:8080'#'192.168.100.11'

AUV_PING_INTERVAL = 6

# Heat Regulation in Pi
SAFE_TEMP = 60
HOT_TEMP = 80
