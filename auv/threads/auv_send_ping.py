from static import global_vars
from static import constants
from api import Radio
import threading
import sys
sys.path.append('..')


# Responsibilites:
#   - send ping

class AUV_Send_Ping(threading.Thread):

    def __init__(self):
        self._ev = threading.Event()

        threading.Thread.__init__(self)

    def run(self):
        """ Main connection loop for the AUV. """

        global_vars.log("Starting main ping sending connection loop.")
        while not self._ev.wait(timeout=constants.PING_SLEEP_DELAY):
            # time.sleep(PING_SLEEP_DELAY)

            if global_vars.radio is None or global_vars.radio.is_open() is False:
                print("in send ping")
                global_vars.connect_to_radio()
                print(global_vars.radio)

            else:
                try:
                    # Always send a connection verification packet
                    constants.RADIO_LOCK.acquire()
                    global_vars.radio.write(constants.PING, 3)
                    # global_vars.radio.write("test")
                    constants.RADIO_LOCK.release()

                except Exception as e:
                    global_vars.radio.close()
                    global_vars.radio = None
                    print("send ping exception")
                    raise Exception("Error occured : " + str(e))
                    # Alw+ str(e))

    def stop(self):
        self._ev.set()
