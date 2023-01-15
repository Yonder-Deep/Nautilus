#!/bin/bash
echo "*** IF first time running startup.sh, exit and start again. ***"
sudo pigpiod
sudo python3 -B ./dev/Nautilus/auv/auv.py
