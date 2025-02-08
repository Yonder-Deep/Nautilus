import ctypes

findRadio = ctypes.cdll.LoadLibrary("./radio.dylib")
findRadio.find_radio.restype = ctypes.c_char_p
print(findRadio.find_radio())