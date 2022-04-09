# System imports
import serial
import time
import threading

# Custom imports
from api import Radio
from static import constants
from static import global_vars


class BaseStation_Send_Ping(threading.Thread):
    def run(self):
        """ Constructor for the AUV """
        self.radio = None

        # Try to assign us a new Radio object
        for rp in constants.RADIO_PATHS:
            try:
                self.radio = Radio(rp['path'])
                print(f"Successfully found radio device on {rp['radioNum']}.")
            except:
                print(f"Warning: Cannot find radio device on {rp['radioNum']}. Trying next radiopath...")

        self.main_loop()

    def main_loop(self):
        """ Main connection loop for the AUV. """
        print("Starting main ping sending connection loop.")
        while True:
            time.sleep(constants.PING_SLEEP_DELAY)

            if self.radio is None or self.radio.is_open() is False:
                print("TEST radio not connected")
                for rp in constants.RADIO_PATHS:
                    try:
                        self.radio = Radio(rp['path'])
                        print(f"Successfully found radio device on {rp['radioNum']}.")
                    except:
                        print(f"Warning: Cannot find radio device on {rp['radioNum']}. Trying next radiopath...")

            else:
                try:
                    # Always send a connection verification packet
                    constants.radio_lock.acquire()
                    self.radio.write(constants.PING)
                    constants.radio_lock.release()

                except Exception as e:
                    raise Exception("Error occured : " + str(e))
