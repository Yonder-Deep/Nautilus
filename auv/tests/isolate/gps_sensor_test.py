import threading
import time
import serial
import pynmea2


class GPS(threading.Thread):
    """Class for basic GPS functionality"""

    def __init__(self):
        threading.Thread.__init__(self)
        self.ser = serial.Serial("COM9", baudrate=9600, timeout=10)
        self.running = True
        self.gps_data = {
            "has_fix": "Unknown",
            "speed": "Unknown",
            "latitude": "Unknown",
            "longitude": "Unknown",
        }

    def parse_gps_data(self, sentence):
        try:
            msg = pynmea2.parse(sentence.decode("utf-8"))
            self.gps_data["has_fix"] = "Yes" if hasattr(msg, "has_fix") else "No"
            self.gps_data["speed"] = (
                msg.speed_knots if hasattr(msg, "speed_knots") else "Unknown"
            )
            self.gps_data["latitude"] = (
                msg.latitude if hasattr(msg, "latitude") else "Unknown"
            )
            self.gps_data["longitude"] = (
                msg.longitude if hasattr(msg, "longitude") else "Unknown"
            )
        except pynmea2.ParseError as e:
            print(f"Error parsing GPS data: {e}")

    def run(self):
        while self.running:
            newdata = self.ser.readline()
            if "$GPRMC" in str(newdata):
                self.parse_gps_data(newdata)
                print(self.gps_data)
            time.sleep(1)

    def stop(self):
        self.running = False
