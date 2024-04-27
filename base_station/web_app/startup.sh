#!/bin/bash
python app.py &


cd React/auv_gui
npm build  &
npm run start 
