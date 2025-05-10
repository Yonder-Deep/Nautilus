from api.localization.main import localize 
from multiprocessing import Process
from threading import Event # Actually using multiprocessing.Event, but type hints break
from multiprocessing.connection import Connection

class Localizer(Process):
    def __init__(self, stop_event: Event, pipe: Connection):
        super().__init__()
        self.stop_event = stop_event
        self.pipe = pipe

    def run(self):
        localize()
