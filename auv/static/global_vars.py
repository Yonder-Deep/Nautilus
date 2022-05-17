import threading
import os
from api import Radio
from static import constants
# determines if connected to BS
connected = False

# Determines if AUV threads should be stopped / restarted
stop_all_threads = False
restart_threads = False

depth_offset = 0

radio = None


def path_existance(radioPaths):
    for rp in radioPaths:
        if os.path.exists(rp['path']):
            return True
    return False


def connect_to_radio():
    global radio
    radio = None
    success_msg = ""
    warning_msg = ""
    for rp in constants.RADIO_PATHS:
        try:
            radio = Radio(rp['path'])
            success_msg += "Successfully found radio device on path " + str(rp['radioNum']) + "."
            break
        except:
            if rp["radioNum"] == 1:
                warning_msg += "Warning: Cannot find radio device on paths " + str(rp['radioNum'])
            else:
                warning_msg += ", " + str(rp['radioNum'])

    if len(success_msg) == 0:
        log(warning_msg)
    else:
        log(success_msg)

    return radio


def log(val):
    print("[AUV]\t" + val)
