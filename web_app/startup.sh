
# !/bin/bash

# Run Backend 
echo "Running app.py..."
python3 app.py &
# opens on http://localhost:6543

cd auv_gui


echo "Running React Frontend"
npm run start
# opens on http://localhost:3000


