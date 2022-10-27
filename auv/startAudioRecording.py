from api import Hydrophone
import time

hydrophone = Hydrophone()

print('start recording')
hydrophone.start("test1.wav")
time.sleep(1)
print('...still recording...')
time.sleep(1)
hydrophone.stop()
print('stop recording')

hydrophone.start("test2.wav")
time.sleep(2)
print('...still recording...')
time.sleep(2)
hydrophone.stop()
print('stop recording')

