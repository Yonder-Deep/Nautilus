from gps_sensor_test import GPS
import time

if __name__ == "__main__":
    gps = GPS()
    gps.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        gps.stop()
        gps.join()
        print("GPS thread stopped.")
