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
    output_msg = ""
    radio = None
    for rp in constants.RADIO_PATHS:
        try:
            radio = Radio(rp['path'])
            output_msg += f"\nSuccessfully found radio device on {rp['radioNum']}."
        except:
            if rp['radioNum'] == 1:
                output_msg += f"Warning: Cannot find radio device on {rp['radioNum']}."
            else:
                output_msg += f", {rp['radioNum']}"
    return radio, output_msg
