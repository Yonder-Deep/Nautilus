# GPS Tester File

# Add parent directory to active path
import time

import sys
import queue

out_queue = queue.Queue()

sys.path.append('../')

# import necessary api to test GPS

try:
    from api import GPS
finally:
    pass

my_gps = GPS(out_queue)
my_gps.start()

# Begin testing
while(True):
    print("Altitude: ", my_gps.altitude)
    print("Latitude: ", my_gps.latitude)
    print("Longitude: ", my_gps.longitude)
    print("Speed: ", my_gps.speed)
    print("Sleeping....\n")
    time.sleep(2)
