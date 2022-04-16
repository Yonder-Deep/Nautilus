from static import global_vars
from static import constants
from api import Radio
import threading
import sys
sys.path.append('..')


# Responsibilites:
#   - send ping

class AUV_Send_Ping(threading.Thread):

    def __init__(self, radio):
        self.radio = radio
        self._ev = threading.Event()

        threading.Thread.__init__(self)

    def run(self):
        """ Main connection loop for the AUV. """

        global_vars.log("Starting main ping sending connection loop.")
        while not self._ev.wait(timeout=constants.PING_SLEEP_DELAY):
            # time.sleep(PING_SLEEP_DELAY)

            if self.radio is None or self.radio.is_open() is False:
                print("TEST radio not connected")
                global_vars.connect_to_radio()

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
