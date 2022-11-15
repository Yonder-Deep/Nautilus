""" This class manages the serial connection between the
AUV and Base Station along with sending controller
commands. """

from static import global_vars
import sys
import os

# System imports
import serial
import time
import math
import argparse
import threading
from queue import Queue

# Custom imports
from api import Crc32
from api import Radio
from api import Joystick
from api import xbox
#from api import NavController
#from api import GPS
from api import decode_command
#from api import checksum
from gui import Main

from threads.base_station_receive import BaseStation_Receive
from threads.base_station_send import BaseStation_Send
from threads.base_station_send_ping import BaseStation_Send_Ping
# Constants
THREAD_SLEEP_DELAY = 0.1  # Since we are the slave to AUV, we must run faster.
PING_SLEEP_DELAY = 3
RADIO_PATH = '/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0'
GPS_PATH = '/dev/serial/by-id/usb-u-blox_AG_-_www.u-blox.com_u-blox_7_-_GPS_GNSS_Receiver-if00'


if __name__ == '__main__':
    """ Main method responsible for developing the main objects used during runtime
    like the BaseStation and Main objects. """

    # Define Queue data structures in order to communicate between threads.
    to_GUI = Queue()
    to_BS = Queue()

    # Create a BS (base station) and GUI object thread.
    #ts = []

    global_vars.connect_to_radio(to_GUI)

    try:
        bs_r_thread = BaseStation_Receive(global_vars.radio, to_BS, to_GUI)
        bs_s_thread = BaseStation_Send(global_vars.radio, to_BS, to_GUI)
        bs_ping_thread = BaseStation_Send_Ping(global_vars.radio, to_GUI)

        # ts.append(bs_r_thread)
        # ts.append(bs_s_thread)
        # ts.append(bs_ping_thread)

        bs_r_thread.start()
        bs_s_thread.start()
        bs_ping_thread.start()
    except Exception as e:
        print("Err: ", str(e))
        print("[MAIN] Base Station initialization failed. Closing...")
        sys.exit()

    # Create main GUI object
    try:
        gui = Main(to_GUI, to_BS)
        gui.root.mainloop()
    except KeyboardInterrupt:
        print("CLOSING")
        gui.root.destroy()
        sys.exit()
