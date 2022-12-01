
import cv2
from time import time
import socket
from goprocam import GoProCamera, constants

gopro = GoProCamera.GoPro(constants.gpcontrol)
# gopro.overview()
gopro.stream("udp://127.0.0.1:10000", quality="high")


# The camera is available on IP 10.5.5.9, with the MAC address AA:BB:CC:DD:EE:FF.


# cap = cv2.VideoCapture("udp://127.0.0.1:10000")
# while True:
#     ret, frame = cap.read()
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     cv2.imshow("GoPro OpenCV", frame)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()
