# Nautilus AUV
Embedded side of the Nautilus AUV
## Running this code
* Install everything with pip. Please use a virtual environment as follows:
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
* Create the TCP/IP connection with PPP (point-to-point protocol) `sudo pppd /dev/tty.usbserial-D30AFALT 57600 nodetach noauth passive lock local 192.168.100.10:192.168.100.11`
* Raspberry Pi OS Lite comes with `pppd`, if you don't have it do `sudo apt-get pppd` or use a package manager to get it
* TODO: Instructions on binding systemd with `udev` to start up automatically
* Ensure that `config.py` has the correct `SOCKET_IP` and `SOCKET_PORT` to communicate with the base station
* Run `python __init__.py` with the virtual environment active
* **To run locally for testing, simply change `SOCKET_IP` to localhost**

## Developing this code
Here is a general map of what everything does:
* `README.md` is self-explanatory
* `__init__.py` is the entry point, and holds the main loop. It spawns off all the other threads.
* `config.py` holds any constants and information that is consumed by `__init__.py` at runtime.
* `core/` holds the main logic threads. `websocket_handler.py` is a thread to handle the websocket connection with the base. `navigation.py` makes high-level navigation decisions and outputs a desired velocity and attitude for the submarine based on its location and what the mission is. `control.py` takes that desired state and runs the control system to get the submarine to that state and keep it there.
* `api/` holds the interfaces for all of the motors, sensors, and other devices that this code needs to interact with.
* `custom_types/` holds all of the `pydantic` types used to validate data and keep things in line.
* `tests/` currently holds a set of test movements, but will soon be migrated to actual code tests.
* `mock_modules/` holds mock python modules, generally consumed by `api/`, that cannot be easily installed on macOS or Windows for real, but are necessary for the real embedded code to function. When running in Linux, these modules are ignored and the real ones are installed and used.

Coding guidelines:
* Don't do anything irreparably stupid
* Keep the flow of imports understandable. If an class instance is needed in `core/`, and is defined in `api/`, instantiate it in `__init__.py` and pass it into the thread you are creating.
* When you create a thread in `__init__.py`, make sure you add it to the `threads` array so that it is cleaned up when the process is quit. Look at `core/websocket_handler.py` for proper thread cleanup when defined as a function, and look at `core/navigation.py` for proper thread cleanup when defined as a class.
* Format functions and classes with docstrings and typed parameters so LSPs can recognize them.
