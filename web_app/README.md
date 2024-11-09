# Nautilus Web App

FastAPI Backend interfacing with AUV
React Frontend bundled and served with Vite

## How to Contribute 

### First Time Setup

- Prerequistes:
    - npm
    - git
    - python (3.x.x)

To install node dependencies, run:
```bash
cd web_app/auv_gui
npm install
```

To startup both the FastAPI Backend and React GUI:
```bash
sh startup.sh
```
(Depending on what python version you have, you may have to edit startup.sh to be python or python3.)

To start the React GUI alone:
```bash
cd web_app/auv_gui
npm start
```
