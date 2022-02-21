import threading
# determines if connected to BS
connected = False

# Determines if AUV threads should be stopped / restarted
stop_all_threads = False
restart_threads = False


def log(val):
    print("[AUV]\t" + val)