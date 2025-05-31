import cv2
import threading
import time
from datetime import datetime

class AUVCamera:
    def __init__(self, cam_path, resolution=(640, 480), fps=50, folder, duration):
        self.cap = cv2.VideoCapture(cam_path, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.fps = fps
        self.resolution = resolution
        self.duration = duration
        self.folder = folder
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.running = self.cap.isOpened()
        if not self.running:
            print(f"Failed to open camera {cam_path}")

        print("Camera initialized.")

    def _record(self):
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'{self.folder}_{timestamp}.mjpg'

        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.out = cv2.VideoWriter(filename, fourcc, self.fps, (self.resolution[0], self.resolution[1]))
        print("Recording started...")

        while self.is_recording:
            ret, frame = self.cap.read()
            if not ret:
                break
            self.out.write(frame)
            time.sleep(1 / self.fps)

        self.out.release()
        print("Recording saved to", filename)

    def start_recording(self):
        if not self.cap:
            raise RuntimeError("Camera not initialized.")
        self.is_recording = True
        self.record_thread = threading.Thread(target=self._record)
        self.record_thread.start()

    def stop_recording(self):
        self.is_recording = False
        if self.record_thread:
            self.record_thread.join()

    def stream(self):
        if not self.cap:
            raise RuntimeError("Camera not initialized.")

        print("Streaming started. Press 'q' to quit.")
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            cv2.imshow('Live Stream', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cv2.destroyAllWindows()

    def release(self):
        if self.cap:
            self.cap.release()
        print("Camera released.")

