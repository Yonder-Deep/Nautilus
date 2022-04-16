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
        self.radio, output_msg = global_vars.connect_to_radio()
        self.log(output_msg)

        self.main_loop()

    def main_loop(self):
        """ Main connection loop for the AUV. """
        print("Starting main ping sending connection loop.")
        while True:
            time.sleep(constants.PING_SLEEP_DELAY)

            if self.radio is None or self.radio.is_open() is False:
                print("TEST radio not connected")
                self.radio, output_msg = global_vars.connect_to_radio()
                self.log(output_msg)
            else:
                try:
                    # Always send a connection verification packet
                    constants.radio_lock.acquire()
                    self.radio.write(constants.PING)
                    constants.radio_lock.release()

                except Exception as e:
                    raise Exception("Error occured : " + str(e))
