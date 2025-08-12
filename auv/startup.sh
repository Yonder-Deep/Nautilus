#!/bin/bash
echo "*** IF first time running startup.sh, exit and start again. ***"
sudo killall pigpiod
sudo pigpiod
source .venv/bin/activate
sudo python -B ./dev/Nautilus/auv/auv.py
