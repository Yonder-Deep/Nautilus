from models.data_types import Log, KinematicState

import cv2

import multiprocessing
from typing import Tuple, Callable, Union
from time import time, sleep
from functools import partial
import os
import signal
import subprocess

def logger(message: str, q: multiprocessing.Queue, verbose: bool):
    if verbose and message:
        q.put(Log(
                source = "PRCP",
                type = "info",
                content = message
        ))

class Perception(multiprocessing.Process):
    def __init__(
        self,
        stop_event: multiprocessing.Event, # type: ignore
        input_q: multiprocessing.Queue,
        camera_path: str,
        ip: str,
        port: int,
        fps: int,
    ):
        super().__init__(name="Perception-Process")
        self.stop_event = stop_event
        self.input_q = input_q
        self.log = partial(logger, q=input_q, verbose=True)
        self.process = subprocess.Popen(
                "gst-launch-1.0 -v v4l2src device=/dev/video0 ! videoconvert ! \
                x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! \
                rtph264pay config-interval=1 pt=96 ! \
                udpsink host=192.168.50.1 port=5000",
                stdout=subprocess.PIPE,
                shell=True,
                preexec_fn=os.setsid
        )

        self.log("Perception streamer launched")

    def run(self):
        while not self.stop_event.set():
            sleep(1)
        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
        self.log("Perception streamer killed")


        """capture = cv2.VideoCapture(filename=camera_path, apiPreference=cv2.CAP_V4L2)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        capture.set(cv2.CAP_PROP_FPS, fps)
        if not capture.isOpened():
            self.log("Error: Could not open camera.")
            exit()
        self.capture = capture

        out = cv2.VideoWriter(
                f'appsrc is-live=true format=GST_FORMAT_PULL ! '
                f'videoconvert ! '
                f'x264enc tune=zerolatency speed-preset=fast ! '
                f'rtph264pay pt=96 config-interval=1 ! '
                f'udpsink host={ip} port={port}',
                cv2.CAP_GSTREAMER,
                0, 
                30, 
                (640, 480), 
                True
        )
        # Check if VideoWriter opened successfully
        if not out.isOpened():
            self.log("Error: Could not open GStreamer pipeline")
        self.out = out
        
        self.max_seconds_per_frame = 1/fps

    def run(self):
        self.log("Perception started")
        last_time = time()
        while True:
            start_time = time()
            if self.stop_event.is_set():
                self.cleanup()
                return
            if time() - last_time > self.max_seconds_per_frame:
                continue

            ret, frame = self.capture.read()
            if not ret:
                continue
            self.out.write(frame)

            last_time = start_time

    def cleanup(self):
        # Cleanup
        self.capture.release()
        self.out.release()
        cv2.destroyAllWindows()"""
