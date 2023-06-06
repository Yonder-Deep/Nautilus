#!/bin/bash

# Install python3 with tkinter.
sudo echo 'Installing python3-tk... (includes Tkinter package for the UI)'
sudo apt-get install python3-tk -y

# Install python3 pip.
echo 'Installing python3-pip... (pip = preferred installer program)'
sudo apt-get install python3-pip -y

# Install all pip modules.
echo 'Installing all pip modules in requirements.txt...'
sudo python3 -m pip install -r requirements.txt

# Install imaging tkinter package
echo 'Installing pil imagetk'
sudo apt-get install python3-pil python3-pil.imagetk

# Install xbox driver
echo 'Installing xbox driver'
sudo apt-get install xboxdrv

echo 'Installation complete!'
