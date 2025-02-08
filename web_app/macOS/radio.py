from ctypes import *
import subprocess

findRadio = cdll.LoadLibrary("./radio.dylib")
findRadio.find_radio.restype = c_void_p
findRadio.free_ptr.argtypes = [c_void_p]
findRadio.free_ptr.restype = None

radioPathBytes = findRadio.find_radio()
print("Radio path: " + str(radioPathBytes))
int_ptr_type = POINTER(c_int)
pathPtr = cast(radioPathBytes, int_ptr_type)
print("Freeing pointer to radio path: " + str(pathPtr))
findRadio.free_ptr(pathPtr)

print("radioPath: " + str(radioPathBytes))