from ctypes import *
import subprocess
import os

findRadio = cdll.LoadLibrary("./radio.dylib")
findRadio.find_radio.restype = c_void_p
findRadio.free_ptr.argtypes = [c_void_p]
findRadio.free_ptr.restype = None

# Call the function, which returns a void pointer
radioPathPtr = findRadio.find_radio()
# Cast the null pointer to a char pointer
# Get the value of the cstring
# Decode the bytes into a python string
radioPath = cast(radioPathPtr, c_char_p).value.decode()

# Free the original void pointer
print("Freeing pointer to radio path: " + str(radioPathPtr))
findRadio.free_ptr(radioPathPtr)

print("Radio path: " + str(radioPath))

if (radioPath and not (radioPath == "Radio device not found")):
    # Symlink named path
    os.symlink(radioPath, "./nautilusRadio")
    print("Named path: " )

    # Launch pppd
    subprocess("pppd", "call", "usbRadio")