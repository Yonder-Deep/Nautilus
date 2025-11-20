import gi
from PIL import Image
import numpy as np

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import threading

import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# Initialize GStreamer
Gst.init(None)

class MJPEGHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/video.mjpg':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            try:
                boundary = b'--jpgboundary\r\n'
                content_type = b'Content-Type: image/jpeg\r\n\r\n'

                #buffer for reading
                buffer = b''

                #read from ffmpeg stdout (passed via server instance)
                while True:

                    #read larger chunks for better performance
                    chunk = self.server.ffmpeg_stdout.read(8192)
                    if not chunk:
                        return
                    
                    buffer += chunk

                    #look for complete JPEG frames (start: FF D8, end: FF D9)
                    while True:
                        #find JPEG start marker
                        start_idx = buffer.find(b'\xff\xd8')
                        if start_idx == -1:
                            #no start marker found, keep only last few bytes (might be partial)
                            buffer = buffer[-1:] if len(buffer) > 0 else b''
                            break

                        #find JPEG end marker after start
                        end_idx = buffer.find(b'\xff\xd9', start_idx + 2)
                        if end_idx == -1:
                            #end marker not found yet, need more data
                            break

                        #complete frame found
                        frame_data = buffer[start_idx:end_idx + 2]
                        buffer = buffer[end_idx + 2:]

                        #send fram with multipart headers
                        self.wfile.write(boundary)
                        self.wfile.write(content_type)
                        self.wfile.write(frame_data)
                        self.wfile.write(b'\r\n')
                        self.wfile.flush()
            except Exception as e:
                print(f"MJPEG handler error: {e}")
                import traceback
                traceback.print_exc()
                pass



def log_stderr(process, name):
        for line in iter(process.stderr.readline, b''):
            if line:
                print(f"[{name} ERROR]: {line.decode('utf-8', errors='ignore')}", file=sys.stderr)

class VideoThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.gst_process = None
        self.ffmpeg_process = None
        self.http_server = None

    def run(self):
        gst_command = [
            'gst-launch-1.0', 
            'udpsrc', 
            'port=5000', 
            'caps=application/x-rtp,media=video,clock-rate=90000,encoding-name=H264,payload=96',
            '!', 'rtph264depay', 
            '!', 'h264parse', 
            '!', 'avdec_h264', 
            '!', 'videoconvert', 
            '!', 'video/x-raw,format=RGB',
            '!', 'fdsink',
            'fd=1'
        ]

        ffmpeg_command = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-pixel_format', 'rgb24', 
            '-video_size', '320x240',
            '-framerate', '30',
            '-i', '-', 
            '-f', 'mjpeg', 
            '-q:v', '3', 
            '-'
        ]

        #starts GStreamer
        self.gst_process = subprocess.Popen( 
            gst_command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            bufsize=0
        )

        self.ffmpeg_process = subprocess.Popen( 
            ffmpeg_command,
            stdin=self.gst_process.stdout, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0
        )

        self.gst_process.stdout.close()

        stderr_thread_gst = threading.Thread(target=log_stderr, args=(self.gst_process, "GST"))
        stderr_thread_ffmpeg = threading.Thread(target=log_stderr, args=(self.ffmpeg_process, "FFMPEG"))
        stderr_thread_gst.daemon = True
        stderr_thread_ffmpeg.daemon = True
        stderr_thread_gst.start()
        stderr_thread_ffmpeg.start()



        #start HTTP server
        self.http_server = HTTPServer(('0.0.0.0', 8081), MJPEGHandler)
        self.http_server.ffmpeg_stdout = self.ffmpeg_process.stdout
        print(f"starting http server on port 8081...")
        self.http_server.serve_forever()

    def quit_loop(self):
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            self.ffmpeg_process.wait()
        if self.gst_process:
            self.gst_process.terminate()
            self.gst_process.wait()