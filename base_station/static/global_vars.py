import os
# Global variables used by the BaseStation threads

connected = False    # boolean that determines if BS has radio connection with AUV


def path_existance(radioPaths):
    for rp in radioPaths:
        if os.path.exists(rp['path']):
            return True
    return False
