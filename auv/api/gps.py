from __future__ import annotations
import threading
from threading import Event
from queue import Queue
import time
import serial
import pynmea2

class GPS(threading.Thread):
    """Class for basic GPS functionality"""

    def __init__(self, out_queue:Queue, path: str, stop_event:Event):
        super().__init__()
        self.stop_event = stop_event
        self.out_queue = out_queue
        self.ser = serial.Serial(path, baudrate=9600, timeout=0.1)

    def run(self):
        while not self.stop_event.is_set():
            try:
                if self.ser.in_waiting > 0:
                    new_data = self.ser.readline().decode()
                    msg = pynmea2.parse(new_data)
                    if type(msg) == pynmea2.types.GLL or type(msg) == pynmea2.types.RMC or type(msg) == pynmea2.types.GLL:
                        print("LAT: " + str(msg.lat) + " LON: " + str(msg.lon) + " TIME: " + str(msg.timestamp))
                        self.out_queue.put(msg)
            except pynmea2.ParseError as e:
                print(f"Error parsing GPS data: {e}")
            except UnicodeDecodeError as e:
                print(f"Error decoding GPS data: {e}")

            time.sleep(0.001)

    def stop(self):
        self.stop_event.set()

if __name__ == "__main__":
    from config import GPS_PATH

    random_queue = Queue()
    stop_event = Event()
    serial_thread = GPS(
        out_queue=random_queue,
        path=GPS_PATH,
        stop_event=stop_event
    )

    try:
        serial_thread.start()
    except KeyboardInterrupt:
        serial_thread.stop()
        serial_thread.join()
        print("Serial thread stopped.")
