import os
from static import constants
from api import Radio
# Global variables used by the BaseStation threads

connected = False    # boolean that determines if BS has radio connection with AUV

radio = None

def path_existance(radioPaths):
    for rp in radioPaths:
        if os.path.exists(rp['path']):
            return True
    return False


def connect_to_radio(queue):
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
        log(queue, warning_msg)
    else:
        log(queue, success_msg)



def log(queue, msg):
    queue.put("log('" + msg + "')")
