# !/bin/bash

# This build script can be rerun without breaking anything, though it will put you in nested virtual environments
# If in a double (.venv), enter 'deactivate' to get out

# Create virtual environment, activate it, and install python requirements
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Run npm script to build react-vite app & generate static bundle
cd frontend_gui 
npm install
npm run build

# Return to original directory
cd ..
