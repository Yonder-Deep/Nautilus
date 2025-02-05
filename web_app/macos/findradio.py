import ctypes
from ctypes import util

iokit = ctypes.cdll.LoadLibrary(ctypes.util.find_library('IOKit'))

kIOMasterPortDefault = ctypes.c_void_p.in_dll(iokit, 'kIOMasterPortDefault')

iokit.IOServiceMatching.restype = ctypes.c_void_p

iokit.IOServiceGetMatchingServices.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
iokit.IOServiceGetMatchingServices.restype = ctypes.c_void_p

serial_port_iterator = ctypes.c_void_p()

print('kIOMasterPortDefault =', str(kIOMasterPortDefault))

response = iokit.IOServiceGetMatchingServices(
    kIOMasterPortDefault,
    iokit.IOServiceMatching(b'kIOUSBDeviceName'),
    ctypes.byref(serial_port_iterator)
)
print('serial_port_iterator =', serial_port_iterator)
