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
    output_msg = ""
    for rp in constants.RADIO_PATHS:
        try:
            radio = Radio(rp['path'])
            output_msg += "\nSuccessfully found radio device on " + str(rp['radioNum'])
            break
        except:
            if rp["radioNum"] == 1:
                output_msg += "Warning: Cannot find radio device on " + str(rp['radioNum'])
            else:
                output_msg += ", " + str(rp['radioNum'])
    print(output_msg)


def log(val):
    print("[AUV]\t" + val)
