import threading
import time
import serial
import pynmea2

GPS_PATH = "COM4"


class GPS(threading.Thread):
    """Class for basic GPS functionality"""

    def __init__(self):
        threading.Thread.__init__(self)
        self.ser = serial.Serial(GPS_PATH, baudrate=9600, timeout=10)
        self.running = True
        self.gps_data = {
            "has_fix": "Unknown",
            "speed": "Unknown",
            "latitude": "Unknown",
            "longitude": "Unknown",
        }

    def parse_gps_data(self, sentence):
        try:
            sentence = sentence.decode("utf-8")
            msg_fields = sentence.split(",")
            msg = pynmea2.parse(sentence)
            # print(msg)
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
                print(self.gps_data)
            time.sleep(1)

    def stop(self):
        self.running = False
