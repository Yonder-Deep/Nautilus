# !/bin/bash

# This build script can be rerun without breaking anything, though it will put you in nested virtual environments
# If in a double (.venv), enter 'deactivate' to get out

# Create virtual environment, activate it, and install python requirements
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Run npm script to build react-vite app & generate static bundle
cd auv_gui
npm install
npm run build

# Return to original directory
cd ..
