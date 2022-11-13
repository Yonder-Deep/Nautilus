import threading
import os
from api import Radio
from static import constants
import sys

sys.path.append(".//")

# determines if connected to BS
connected = False

# Determines if AUV threads should be stopped / restarted
stop_all_threads = False
restart_threads = False

depth_offset = 0

radio = None

sending_dive_log = False
file_packets_sent = 0
file_packets_received = 0
bs_response_sent = False


def path_existance(radioPaths):
    for rp in radioPaths:
        if os.path.exists(rp['path']):
            return True
    return False


def connect_to_radio():
    global radio
    success_msg = ""
    warning_msg = ""
    for rp in constants.RADIO_PATHS:
        try:
            radio = Radio(rp['path'])
            success_msg += "Successfully found radio device on path " + str(rp['radioNum']) + "."

            break
        except Exception as e:
            if rp["radioNum"] == 1:
                warning_msg += "Warning: Cannot find radio device on paths " + str(rp['radioNum'])
            else:
                warning_msg += ", " + str(rp['radioNum'])
    if len(success_msg) == 0:
        log(warning_msg)
    else:
        log(success_msg)
        print(radio)


def log(val):
    print("[AUV]\t" + val)
