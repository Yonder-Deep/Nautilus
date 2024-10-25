#!/bin/bash

# This script is used to start the web application for the Nautilus base station.

# Start the Python Flask server by running the app.py script in the background.
python app.py &

# Change directory to the React/auv_gui folder.
cd React/auv_gui

# Build the React application in the background.
# npm run build &

# Start the React development server.
npm run start

