# Nautilus Web App

Consists of:
* React frontend bundled with Vite to static files
* FastAPI backend serves react static files and interfaces with AUV

Important notes:
* When running, find the GUI at http://localhost:6543/index.html
* All commands henceforth assume that the starting directory is web_app, wherein lies this README.md file.

## How to Contribute 

### First Time Setup

- Prerequistes:
    - npm
    - git
    - python (3.x.x)

To start, just run:
```bash
# On Linux/Mac Systems:
cd web_app
. build.sh

# On Windows:
cd web_app
./build_win.bat
```
It will create a python virtual environment, activate it, install the required python scripts, then install the npm dependencies and build the static files for the React frontend with vite.
If you run into problems with the build script, open it and troubleshoot with the comments in there.
You can rerun build.sh without breaking stuff.

To start the app, you can do either:
```bash
# Mac/Linux
. startup.sh
# Windows
./startup_win.bat
```
or
```bash
python3 app.py
```
Depending on what python version you have, you may have to edit startup.sh to be python or python3.
If you get errors about python modules not being loaded, ensure the virtual environment is activated via:
```bash
# Mac/Linux
. .venv/bin/activate
# Windows
.\.venv\Scripts\activate
```
For other runtime dependency issues, open build.sh and troubleshoot from there.

To start the React GUI alone:
(Has hot module replacement, good for developing the GUI alone)
```bash
cd auv_gui
npm start
```

### Useful Resources:
- Obviously, MDN Web Docs at `https://developer.mozilla.org/en-US/docs/Web/JavaScript`
- For React, `https://react.dev/reference/react`
- For icons and fonts, go to `https://fonts.google.com/`
- For general Python, go to `https://docs.python.org/3/`
- For messing with FastAPI in `__init__.py`, go to `https://fastapi.tiangolo.com/reference/`
- For messing with the backend websocket handler (not the FastAPI websocket), go to `https://websockets.readthedocs.io/en/stable/`
- For information about `ppp`, do `man pppd` or go to `https://linux.die.net/man/8/pppd`. If you end up on these man pages, you better start praying.
