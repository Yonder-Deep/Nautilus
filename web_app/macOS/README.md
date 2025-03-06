# PPP Connection on macOS
## This directory is for easily creating the ppp (point to point protocol) connection over the USB radio
### Conceptually:
- `radio.m` is an Objective-C script that uses IOKit from macOS to obtain the path (as in `/dev/tty.usbserial-MY_RADIO`)
- This is compiled with clang into a dynamic library (`.dylib`) or into an executable (`.exe`)
- We then run the `pppd` command to start ppp on the device at the `/dev/..` path we just found
- On macOS the `pppd` command is found at `/usr/sbin/pppd`. Man page can also be found here: `https://linux.die.net/man/8/pppd`
- The full command is `pppd [path-to-radio] 57600 nodetach lock local 192.168.100.10:192.168.100.11`

I don't recommend the following implementation, as it would require giving the python script sudo privilege. Just use `radio.exe`.
- This makes it accessible to `radio.py`, which can load the library and call the functions inside using the built-in python module `ctypes`
- `ctypes` was not used directly with IOKit from macOS because that library has not been wrapped/bridged to python
- From `radio.py` we use the subprocess module to execute the `pppd` command with a bunch of options to create a TCP/IP connection
### Usage:
- Compile `radio.m` to an `.exe` for testing with: `clang -framework Foundation -framework IOKit radio.m -o radio.exe`
Don't use the python implementation below:
- Compile `radio.m` to a `.dylib` for for python's use with: `clang -framework Foundation -framework IOKit -dynamiclib radio.m -o radio.dylib`
- Make sure you have XCode Developer Tools installed
