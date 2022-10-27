from api import Hydrophone
import time

hydrophone = Hydrophone()

print('start recording')
hydrophone.start()
time.sleep(1)
print('...still recording...')
time.sleep(1)
hydrophone.stop()
print('stop recording')
