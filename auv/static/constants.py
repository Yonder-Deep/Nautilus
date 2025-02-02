# Communication with base
SOCKET_IP= "localhost"#"192.168.100.10"
SOCKET_PORT=8080
PING_INTERVAL=6 

# Constants for the AUV
# encode sizes and generalizations
IMU_PATH = "/dev/serial0"
IMU_RESET_PIN = 8

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

DIVE_LOG = "dive_log.txt"