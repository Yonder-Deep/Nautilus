from api.localization import localize, localize_setup

from multiprocessing import Process
from multiprocessing.queues import Queue
from threading import Event # Actually using multiprocessing.Event, but type hints break
from time import time
import math

class Localization(Process):
    def __init__(self, stop_event: Event, output_q: Queue):
        super().__init__()
        self.stop_event = stop_event
        self.output_q = output_q

    def run(self):
        localizer_classes = localize_setup()
        current_time = time()
        ekf = localizer_classes[4]
        while True:
            if self.stop_event.is_set():
                return
            quat, current_time = localize(current_time, *localizer_classes)
            lat = math.degrees(ekf.get_latitude_rad())
            lon = math.degrees(ekf.get_longitude_rad())
            self.output_q.put((quat,lat,lon))
