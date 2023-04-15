from api import Hydrophone
import time

hydrophone = Hydrophone()

# print('start recording')
# hydrophone.start_recording()
# time.sleep(1)
# print('...still recording...')
# time.sleep(1)
# hydrophone.stop_recording()
hydrophone.start_recording_for(10)
