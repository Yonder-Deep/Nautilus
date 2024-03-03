import threading
import time
import serial
import string
import pynmea2
from static.constants import GPS_PATHS


class GPS(threading.Thread):
    """Class for basic GPS functionality"""

    def __init__(self, out_queue):
        threading.Thread.__init__(self)
        self.out_q = out_queue
        self.running = False
        self.gps_data = {
            "has_fix": "Unknown",
            "speed": "Unknown",
            "latitude": "Unknown",
            "longitude": "Unknown",
        }
        for gps_path in GPS_PATHS:
            try:
                self.ser = serial.Serial(gps_path, baudrate=9600, timeout=10)
                self.running = True
                break
            except:
                print("No gps found.")

    def parse_gps_data(self, sentence):
        try:
            sentence = sentence.decode("utf-8")
            msg_fields = sentence.split(",")
            msg = pynmea2.parse(sentence)
            print(msg)
            self.gps_data["has_fix"] = "Yes" if msg_fields[2] == "A" else "No"
            self.gps_data["speed"] = (
                msg_fields[7] if msg_fields[7] != "0.0" else "Unknown"
            )
            self.gps_data["latitude"] = (
                str(msg.latitude) if hasattr(msg, "latitude") else "Unknown"
            )
            self.gps_data["longitude"] = (
                str(msg.longitude) if hasattr(msg, "longitude") else "Unknown"
            )
        except pynmea2.ParseError as e:
            print(f"Error parsing GPS data: {e}")
        except UnicodeDecodeError as e:
            print(f"Error decoding GPS data: {e}")

    def run(self):
        while self.running:
            newdata = self.ser.readline()
            if b"$GPRMC" in newdata:
                self.parse_gps_data(newdata)
                self.out_q.put(self.gps_data)
            time.sleep(1)

    def stop(self):
        self.running = False
