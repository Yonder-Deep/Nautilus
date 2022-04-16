import os
import constants
from api import Radio
# Global variables used by the BaseStation threads

connected = False    # boolean that determines if BS has radio connection with AUV


def path_existance(radioPaths):
    for rp in radioPaths:
        if os.path.exists(rp['path']):
            return True
    return False


def connect_to_radio(self, radio):
    for rp in constants.RADIO_PATHS:
        try:
            radio = Radio(rp['path'])
            self.log(f"Successfully found radio device on {rp['radioNum']}.")
        except:
            if rp['radioNum'] == 1:
                self.log(f"Warning: Cannot find radio device on {rp['radioNum']}.")
            else:
                self.log(f", {rp['radioNum']}", end="")
