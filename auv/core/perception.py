from models.data_types import Log, logger
from models.tasks import PTask

import multiprocessing
from functools import partial
import os
import signal
import subprocess

class Perception(PTask):
    def __init__(
        self,
        logging_q: multiprocessing.Queue,
        camera_path: str,
        ip: str,
        port: int,
        fps: int,
    ):
        super().__init__(name="Perception-Process")
        self.logging_q = logging_q
        self.log = partial(logger, q=logging_q, source="PRCP", verbose=True)
        self.path = camera_path
        self.host = ip
        self.port = port
        self.fps = fps

    def run(self):
        process=subprocess.Popen(
                f"gst-launch-1.0 -v v4l2src device={self.path} ! videoconvert \
                ! x264enc tune=zerolatency bitrate=500 speed-preset=superfast \
                ! rtph264pay config-interval=1 pt=96 ! udpsink \
                host={self.host} port={self.port}",
                stdout=subprocess.PIPE,
                shell=True,
                preexec_fn=os.setsid
        )
        self.log("Perception streamer launched")
        # Block until event is cleared
        self.meta.started_event.wait() # type: ignore
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        self.log("Perception streamer killed")
