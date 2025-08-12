# Nautilus Web App

## Quick Start
* Ensure system dependencies: `python3.9+` with `pip`, and `nodejs` with `npm`.
* If you would like to change any of the configuration options (scroll for reference), do `cp ./data/config.yaml ./data/local/`, and override anything that you would like to.
* Establish a IP interface between the machine running this base station code and the machine running the AUV code. This can be done with Wi-Fi, Wi-Fi HaLow, Ethernet, PPP over a serial port, or any other method.
* If running both sides locally, communicating over `localhost` will work perfectly fine.
* If on MacOS, run `build.sh` and `startup.sh`.
* If on Windows, run `build_win.bat` and `startup_win.bat`.
* Navigate to http://localhost:6543 on any browser

## Contributing
The base station web app consists of:
* React frontend bundled by Vite into to static HTML/JS/CSS files. This happens in `frontend_gui/`, and the static files are output into `frontend_gui/dist/`.
* FastAPI Python web server serves those static files and interfaces with the AUV code.
* Python entrypoint is `__init__.py`, the command and data communication is done via a separate websocket thread in `backend.py`, and video streaming is done via a separate thread in `video.py`.
* Video streaming currently not easily available in MacOS, since `gstreamer` is difficult to compile on MacOS. Will switch to `ffmpeg`, which is easy to build on MacOS.

To develop the React GUI with no backend:
(Has hot module replacement and [`react-scan`](https://github.com/aidenybai/react-scan), good for developing the GUI alone)
```bash
cd frontend_gui/
npm start
```

### Useful Resources:
- Obviously, MDN Web Docs at https://developer.mozilla.org/en-US/docs/Web/JavaScript
- For React, https://react.dev/reference/react
- For icons and fonts, go to https://fonts.google.com/
- For general Python, go to https://docs.python.org/3/
- For messing with FastAPI in `__init__.py`, go to https://fastapi.tiangolo.com/reference/
- For messing with the backend websocket handler (not the FastAPI websocket), go to https://websockets.readthedocs.io/en/stable/
- For information about `pppd`, do `man pppd` or go to https://linux.die.net/man/8/pppd.
