import os
from static import constants
from api import Radio
# Global variables used by the BaseStation threads

connected = False    # boolean that determines if BS has radio connection with AUV


def path_existance(radioPaths):
    for rp in radioPaths:
        if os.path.exists(rp['path']):
            return True
    return False


def connect_to_radio():
    success_msg = ""
    warning_msg = ""
    radio = None
    for rp in constants.RADIO_PATHS:
        try:
            radio = Radio(rp['path'])
            success_msg += "Successfully found radio device on path " + str(rp['radioNum'])
            return radio, success_msg
            break
        except:
            if rp['radioNum'] == 1:
                warning_msg += "Warning: Cannot find radio device on paths " + str(rp['radioNum'])
            else:
                warning_msg += ", " + str(rp['radioNum'])
    return radio, warning_msg
