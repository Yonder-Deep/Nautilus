import os
from static import constants
from api import Radio
# Global variables used by the BaseStation threads

connected = False    # boolean that determines if BS has radio connection with AUV

radio = None
downloading_file = False
file_size = 0
file_packets_received = 0
packet_received = False
in_autonomous_nav = False

def path_existance(radioPaths):
    for rp in radioPaths:
        if os.path.exists(rp['path']):
            return True
    return False

def connect_to_radio(queue, verbose: bool):
    def log(queue, msg, verbose_option):
        if verbose_option:
            queue.put(msg)
    
    global radio
    success_msg = ""
    warning_msg = ""
    for rp in constants.RADIO_PATHS:
        try:
            radio = Radio(rp['path'])
            success_msg += "Successfully found radio device on path " + str(rp['radioNum'])
            break
        except:
            if rp['radioNum'] == 1:
                warning_msg += "Warning: Cannot find radio device on paths " + str(rp['radioNum'])
            else:
                warning_msg += ", " + str(rp['radioNum'])

    if len(success_msg) == 0:
        log(queue, warning_msg, verbose)
    else:
        log(queue, success_msg, verbose)

def log(queue, msg):
    queue.put(msg)