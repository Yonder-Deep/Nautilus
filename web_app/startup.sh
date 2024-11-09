# !/bin/bash

# Run Backend 
echo "Running app.py Server"
python3 app.py
# Opens on http://localhost:6543

# Serve static frontend files
cd auv_gui
echo "Running React Frontend"
npm start
# Opens on http://localhost:3175
