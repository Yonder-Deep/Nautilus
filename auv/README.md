# Nautilus AUV
Embedded side of the Nautilus AUV

## Running this code
* Install everything with pip. Use a virtual environment as follows:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
* If you would like to change any of the configuration options (scroll for reference), do `cp ./data/config.yaml ./data/local/`, and override anything that you would like to.
* Establish a route between the machine running this code with the base station machine running the web app with an IP address. This can be done with Wi-Fi, Wi-Fi HaLow, Ethernet, PPP over a serial port, or any other method.
* If developing locally, everything is already defaulted to `localhost`.
* If using real motor controller, start the gpio daemon with `sudo pigpiod`.
* With the virtual environment active, run `python __init__.py`.

### Configuration options:
* "simulation": `boolean` -- Whether or not to use the real motor controller or write to a simulated version of the AUV.
* "socket_ip": `string` -- The ip address or hostname to host the WebSocket server on for communication. Ensure that this is consistent with the port to that the base station will attempt to connect to.
* "socket_port": `int` -- The port to host on. Ensure that this is consistent with the port to that the base station will attempt to connect to.
* "ping_interval": `int` -- Currently unused.
* "gps_path": `string` -- The filepath to the gps device.
* "perception": `boolean` -- Whether or not to create the perception task, which deals with perception of the surroundings via camera(s).
* "video_ip": `string` -- The ip address or hostname on the *base station* that video will be streamed to. Only has effect when "perception" is set to `true`.
* "video_port": `string` -- The port on the *base station* that video will be streamed to. Only has effect when "perception" is set to `true`.
* "camera_path": `string` -- The filepath to the camera.

## Developing this code
### Here is a general map of what everything does:
* `README.md` obviously
* `__init__.py` is the entry point, and holds the main loop. It spawns off all the other threads.
* `core/` holds the main "tasks", whic may be threads or processes. 
    * `websocket_handler.py` is a thread to handle the websocket connection with the base. 
    * `navigation.py` makes high-level navigation decisions and outputs a desired velocity and attitude for the submarine based on its location and what the mission is.
    * `control.py` takes that desired state and runs the control system to get the submarine to that state and keep it there.
    * `localization.py` tries to estimate the current state of the system (position, attitude, and their derivatives)
    * `perception.py` deals with perceiving and coordinating reactions to the surroundings
    
* `api/` holds the interfaces for all of the motors, sensors, and other devices that this code needs to interact with.
* `models/` holds common datatypes, objects, shared memory, and utilities.
* `data/` holds all configuration data that is not code.
* `data/local/` holds locally overriden or collected data that is not meant to upstreamed to the repository.
* `tests/` currently holds a set of test movements, but will soon be migrated to actual code tests.
* `mock_modules/` holds mock python modules, generally consumed by `api/`, that cannot be easily installed on macOS or Windows for real, but are necessary for the real embedded code to function. When running in Linux, these modules are ignored and the real ones are installed and used. (Getting rid of this soon)

### Coding guidelines:
* Don't do anything irreparably stupid.
* Keep the flow of imports understandable. If the instance of a class is needed in `core/`, and that class is defined in `api/`, don't instantiate it in the task in `core/`. Instead instantiate it in `__init__.py` and then pass it into the constructor for the task.
* When you create a task in `__init__.py`, make sure you add it to the `tasks` array so that it is cleaned up when the process is quit. Look at `core/websocket_handler.py` for proper thread cleanup when defined as a function, and look at `core/navigation.py` for proper thread cleanup when defined as a class.
* Format functions and classes with docstrings and typed parameters so LSPs can recognize them.

