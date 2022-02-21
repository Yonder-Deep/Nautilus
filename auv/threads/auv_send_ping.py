<<<<<<< HEAD
import sys
sys.path.append('..')

import threading

from api import Radio

from static import constants
from static import global_vars

# Responsibilites:
#   - send ping
=======
from static import global_vars
from static import constants
from api import Radio
import threading
import sys
sys.path.append('..')


# Responsibilites:
#   - send ping

>>>>>>> develop
class AUV_Send_Ping(threading.Thread):

    def __init__(self):
        self.radio = None
        self._ev = threading.Event()

        threading.Thread.__init__(self)

    def _init_hardware(self):
        """ Radio initializer for the AUV """

        try:
            self.radio = Radio(constants.RADIO_PATH)
            global_vars.log("Radio device has been found.")
        except:
            global_vars.log("Radio device is not connected to AUV on RADIO_PATH.")

    def run(self):
        """ Main connection loop for the AUV. """

<<<<<<< HEAD
        self._init_hardware()
=======
       self._init_hardware()
>>>>>>> develop

        global_vars.log("Starting main ping sending connection loop.")
        while not self._ev.wait(timeout=constants.PING_SLEEP_DELAY):
            # time.sleep(PING_SLEEP_DELAY)

            if self.radio is None or self.radio.is_open() is False:
                print("TEST radio not connected")
                try:  # Try to connect to our devices.
                    self.radio = Radio(constants.RADIO_PATH)
                    global_vars.log("Radio device has been found!")
                except Exception as e:
                    global_vars.log("Failed to connect to radio: " + str(e))

            else:
                try:
                    # Always send a connection verification packet
                    constants.RADIO_LOCK.acquire()
                    self.radio.write(constants.PING, 3)
                    constants.RADIO_LOCK.release()

                except Exception as e:
                    raise Exception("Error occured : " + str(e))

    def stop(self):
        self._ev.set()
