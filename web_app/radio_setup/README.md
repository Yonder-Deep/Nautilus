# PPP Connection Instructions 
This directory is for creating the ppp (point to point protocol) connection over the USB radio between the base station and the AUV. We will be using the [pppd (point-to-point protocol Daemon)](https://linux.die.net/man/8/pppd). 

Currently, we support setting up a ppp connection only for Windows (WSL) and MacOS. 

## Windows (WSL) 
- Connect your radio to a serial port. 
- Use [usbipd](https://learn.microsoft.com/en-us/windows/wsl/connect-usb) to attach the radio to WSL so that you can access it in WSL. 
  - You can check if the radio is detected in WSL by running `lsusb`
- First, on the AUV-side (Raspberry Pi) start a pppd connection with `sudo pppd [path to radio] 57600 lock local noauth 192.168.100.11:192.168.100.10`
  - `[path to radio]` is often `/dev/ttyUSB0`    
  - `57600` = baud rate 
  - `lock` = Ensures exclusive access to the device that uses this connection 
  - `local` = non-modem
  - `noauth` = don't require authentication 
  - `IP1 : IP2` = local IP : remote IP
- Then, on the base station (WSL), connect to the pi with `sudo pppd [path to radio] 57600 lock local noauth nodetach 192.168.100.10:192.168.100.11` 
  - `nodetach` = don't run the command in the background (i.e. it's fine if the terminal gets locked on this process)
- You will know that the connection is successful, if the devices and IPs appear in your WSL terminal 

Some useful commands: 
- `lsusb` = see what serial devices are detected by WSL 
- `ps aux | grep pppd` = checks if a pppd process is running 

## MacOS
#### Conceptually:
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
