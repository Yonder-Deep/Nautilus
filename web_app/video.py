import gi
from PIL import Image
import numpy as np

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

from queue import Queue
import threading

# Initialize GStreamer
Gst.init(None)

class VideoThread(threading.Thread):
    def __init__(self, output_q):
        super().__init__()
        self.output_q = output_q

        pipeline = Gst.parse_launch(
            'udpsrc port=5000 caps="application/x-rtp, media=video, encoding-name=H264, payload=96" '
                '! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! video/x-raw,format=RGB ! appsink name=sink emit-signals=true max-buffers=1 drop=true'
        )
        appsink = pipeline.get_by_name("sink")
        appsink.connect("new-sample", self._on_new_sample)
        pipeline.set_state(Gst.State.PLAYING)

        self.loop = GLib.MainLoop()

    def run(self):
        print("GLib Main Loop starting...")
        self.loop.run()
        print("GLib Main Loop stopped.")

    def quit_loop(self):
        if self.loop:
            print("Scheduling loop quit...")
            # Schedule the quit operation to be executed in the main loop's thread
            GLib.idle_add(self._do_quit)

    def _do_quit(self):
        print("Quitting GLib Main Loop...")
        self.loop.quit()
        return GLib.SOURCE_REMOVE # Ensure this source is removed after executing

    def _on_new_sample(self, sink):
        sample = sink.emit("pull-sample")
        if sample:
            buf = sample.get_buffer()
            caps = sample.get_caps()
            structure = caps.get_structure(0)
            width = structure.get_value("width")
            height = structure.get_value("height")

            success, map_info = buf.map(Gst.MapFlags.READ)
            if success:
                data = map_info.data

                # Convert raw RGB data to NumPy array
                arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 3))
                self.output_q.put(arr)

                buf.unmap(map_info)

        return Gst.FlowReturn.OK
