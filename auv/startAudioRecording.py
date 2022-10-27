# from api import Hydrophone
# import time

# hydrophone = Hydrophone()

# print('start recording')
# hydrophone.start()
# time.sleep(1)
# print('...still recording...')
# time.sleep(1)
# hydrophone.stop()
# print('stop recording')

# based on arbitrary duration example
import queue, threading, sys, time
import sounddevice as sd
import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)

f = "/tmp/rec_threading.wav"

subtype = 'PCM_16'
dtype = 'int16' 

q = queue.Queue()
recorder = False

def rec():
    with sf.SoundFile(f, mode='w', samplerate=44100, 
                      subtype=subtype, channels=1) as file:
        with sd.InputStream(samplerate=44100.0, dtype=dtype, 
                            channels=1, callback=save):
            while getattr(recorder, "record", True):
                file.write(q.get())

def save(indata, frames, time, status):
    q.put(indata.copy())

def start():
    global recorder
    recorder = threading.Thread(target=rec)
    recorder.record = True
    recorder.start()

def stop():
    global recorder
    recorder.record = False
    recorder.join()
    recorder = False

# main
print('start recording')
start()
time.sleep(1)
print('...still recording...')
time.sleep(1)
stop()
print('stop recording')

