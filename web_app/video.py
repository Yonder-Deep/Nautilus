import gi
from PIL import Image
import numpy as np

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

from queue import Queue
import threading

import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

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
            'gst-launch-1.0', #gst-launch-1.0 launches gstreamer version 1.0; 
            'udpsrc', #GStreamer reads from UDP socket
            'port=5000', 
            'caps=application/x-rtp,media=video,encoding-name=H264,payload=96',
            #application/x-rtp is the RTP protocol format
            #payLoad=96 is the RTP payload type (96 is the standard for H.264)
            '!', 'rtph264depay', #! is the pipeline connector; depay extracts H.264  NAL units from RTP packets
            '!', 'h264parse', #parses H.264 bitstream
            '!', 'avdec_h264', #H.264 decoder which decodes H.264 into raw video frames
            '!', 'videoconvert', #converts video
            '!', 'video/x-raw,format=RGB', #specifies format of raw uncompressed video and RGB pixel format
            '!', 'fdsink', #writes frames to file descriptor (stdout)
            'fd=1' #file descriptor is 1 (stdout)
        ]

        ffmpeg_command = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-pixel_format', 'rgb24', #24-bit RGB with 8 bits for red, green, and blue per pixel
            '-video_size', '640x480',
            '-framerate', '30',
            '-i', '-', #-i is input file/stream and - reads from stdin which is connected to the file descriptor from GStreamer
            '-f', 'mjpeg', #each frame is a JPEG
            '-q:v', '3', #quality of video goes from 1-31 with lower=better quality
            '-'
        ]

        #starts GStreamer
        self.gst_process = subprocess.Popen( #Popen(Process Open) starts gst_command as new separate process
            gst_command, 
            stdout=subprocess.PIPE, #PIPE is connection between processes so they can send each other data
            stderr=subprocess.PIPE,
            bufsize=0
        )

        #starts ffmpeg and pipes GStreamer stdout to ffmpeg stdin
        self.ffmpeg_process = subprocess.Popen( #same as gst_process but for ffmpeg
            ffmpeg_command,
            stdin=self.gst_process.stdout, #ffmpeg reads from GStreamer stdout
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0
        )

        #close GStreamer stdout - ffmpeg now owns the pipe
        self.gst_process.stdout.close()

        #start stderr logging threads before starting HTTP server to avoid race conditions
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