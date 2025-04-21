# Nautilus
Repository for the [YonderDeep](https://www.yonderdeep.org/) Nautilus AUV.

## Basics
The codebase is split among two machines: 
  * a base station (a Windows 10 / macOS / Linux machine)
  * Nautilus (an AUV with a Raspberry Pi 3 running Raspbian)

## Style Guidlines
Development will be done in Python3 using the [PEP8](https://pep8.org) style guidelines (VSCode strongly encouraged).
  * Uses spaces (4 per indentation) instead of tabs.
  * Utilizes the [autopep8](https://pypi.org/project/autopep8/0.8/extension) for automatic formatting.

Feel free to use the included settings.json file for VSCode development
  * Automatically enables autopep8 functionality with VSCode
  * Format-on-save enabled by default.
  * Python linting disabled by default. (a runtime language like python should not rely on linting)

## Base Station
The base station communicates with the AUV over a radio plugged into a serial USB port. A TCP/IP connection is initiated and maintained over the serial interface, and the 

# Nautilus (the AUV)
A practical, 3D-printed multi-mission modular AUV, housing many sensors including pressure, audio (hydrophones), and GPS. It can also be adapted to implement sonar, salinity, PH, and temperature sensors.

## Hardware:
A fully assembled, 3D-printed Nautilus AUV also includes:

    Raspbery Pi 3 running Raspbian
    915 MHz Radio
    GPS Sensor
    Pressure sensor
    BNO055 IMU (intertial measurement unit)
    4 Underwater motors (Blue Robotics)
    Blue Robotics End-Caps
    Various acoustic acquisitions devives (made from ADC's and MCU's)

NOTE: that this does NOT include specialized YonderDeep PCBs, PDMs, batteries, or cables.

## System Dependencies:
