# from traceback import format_exc
# from static import global_vars
# import sounddevice as sd
# from scipy.io.wavfile import write
# from datetime import datetime
# from static import constants

# class Hydrophone:
#     def __init__(self):
#         self.fs = 62000  # Sample rate
#         self.audio_recording = None

#     def start_record(self, recording_seconds):
#         self.audio_recording = sd.rec(int(recording_seconds * self.fs), samplerate=self.fs, channels=2)
#         sd.wait()
#         self.save_recording()

#     def save_recording(self):
#         write(f'{self.get_new_audio_file_name()}', self.fs, self.audio_recording)  # Save as WAV file

#     def get_new_audio_file_name(self):
#         unformated_time_stamp = datetime.now().isoformat().split(":")
#         formated_time_stamp = ""
#         for part in unformated_time_stamp:
#             formated_time_stamp+=part+"."
#         filename = constants.AUDIO_FOLDER_PATH + formated_time_stamp + "wav"
#         return filename

#     def get_most_recent_recording(self):
#         return self.audio_recording

#     def record(self):
#         try:
#             with sf.SoundFile(self.filepath,
#                                         mode='x', samplerate=self.SAMPLE_RATE,
#                                         channels=self.CHANNELS, subtype=None) as file:
#                 with sd.InputStream(samplerate=self.SAMPLE_RATE, device=self.mic_id,
#                                             channels=self.CHANNELS, callback=self.callback):
#                     global_vars.log(f"New recording started: {self.sound_file.name}")
#                     try:
#                         while True:
#                             file.write(self.mic_queue.get())
#                     except RuntimeError as re:
#                         global_vars.log(f"{re}. If recording was stopped by the user, then this can be ignored")
#         except:
#             global_vars.log(f"Recording failed")


# based on arbitrary duration example
import queue, threading, sys, time
import sounddevice as sd
import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)

class Hydrophone:
    def __init__(self):

        self.f = "rec_threading.wav"

        self.subtype = 'PCM_16'
        self.dtype = 'int16' 

        self.q = queue.Queue()
        self.recorder = False

    def rec(self):
        with sf.SoundFile(self.f, mode='w', samplerate=44100, 
                        subtype=self.subtype, channels=1) as file:
            with sd.InputStream(samplerate=44100.0, dtype=self.dtype, 
                                channels=1, callback=self.save):
                while getattr(self.recorder, "record", True):
                    file.write(self.q.get())

    def save(self, indata, frames, time, status):
        self.q.put(indata.copy())

    def start(self, name):
        self.f = name
        self.recorder = threading.Thread(target=self.rec)
        self.recorder.record = True
        self.recorder.start()

    def stop(self):
        self.recorder.record = False
        self.recorder.join()
        self.recorder = False