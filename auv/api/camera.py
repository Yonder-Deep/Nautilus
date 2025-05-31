import cv2
import threading

class CameraCapture(threading.Thread):
    def __init__(self, cam_path, width=1280, height=720, fps=60):
        self.cap = cv2.VideoCapture(cam_path, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.running = self.cap.isOpened()
        if not self.running:
            print(f"Failed to open camera {cam_path}")

    def stop(self):
        self.running = False
        self.cap.release()
        cv2.destroyAllWindows()