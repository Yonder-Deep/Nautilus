import queue, threading, sys, time
import sounddevice as sd
import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)
import datetime
from static import constants

class Hydrophone:
    def __init__(self):
        self.filename = ""
        self.subtype = 'PCM_16'
        self.dtype = 'int16' 
        self.q = queue.Queue()
        self.recorder = False
    
    def generate_new_audio_file_name(self):
        unformated_time_stamp = datetime.now().isoformat().split(":")
        formated_time_stamp = ""
        for part in unformated_time_stamp:
            formated_time_stamp+=part+"."
        filename = constants.AUDIO_FOLDER_PATH + formated_time_stamp + "wav"
        self.filename = filename

    def rec(self):
        with sf.SoundFile(self.filename, mode='w', samplerate=44100, 
                        subtype=self.subtype, channels=1) as file:
            with sd.InputStream(samplerate=44100.0, dtype=self.dtype, 
                                channels=1, callback=self.save_recording):
                while getattr(self.recorder, "record", True):
                    file.write(self.q.get())

    def save_recording(self, indata, frames, time, status):
        self.q.put(indata.copy())

    def start_recording(self):
        self.generate_new_audio_file_name()
        self.recorder = threading.Thread(target=self.rec)
        self.recorder.record = True
        self.recorder.start()

    def stop_recording(self):
        self.recorder.record = False
        self.recorder.join()
        self.recorder = False