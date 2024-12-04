import time
import threading

from static import constants
from static import global_vars

class Ping_Thread(threading.Thread):
    def __init__(self, radio, out_q=None):
        self.radio = radio
        self.out_q = out_q
        self._stop_event = threading.Event()
        threading.Thread.__init__(self)
        custom_log("Ping thread initialized.")

    def run(self):
        custom_log("Starting main ping sending connection loop.")
        while not self._stop_event.is_set():
            time.sleep(constants.PING_SLEEP_DELAY)
            custom_log("Trying to send ping")
            # will break if global_vars.radio is ever None please add check for that at some point
            if global_vars.radio is not None:
                is_radio_open = global_vars.radio.is_open()
            if global_vars.radio is None or is_radio_open is False:
                custom_log("TEST radio not connected")
                global_vars.connect_to_radio(self.out_q, verbose=True)
            else:
                try:
                    # Always send a connection verification packet
                    if not global_vars.downloading_file:
                        constants.radio_lock.acquire()
                        global_vars.radio.write(constants.PING)
                        constants.radio_lock.release()

                except Exception as e:
                    custom_log("Exception thrown in bs send ping")

    def stop(self):
        self._stop_event.set()

    def join(self, timeout=None):
        self.stop()
        super(Ping_Thread, self).join(timeout)
    
def custom_log(message: str):
        print("\033[33mPING:\033[0m " + message)
