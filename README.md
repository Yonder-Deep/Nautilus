# Nautilus
Repository for the [YonderDeep](https://www.yonderdeep.org/) 2020-2022 Nautilus AUV (Autonomous Underwater Vehicle) developed in the MESOM Laboratory at the Scripps Institution of Oceanography, UC San Diego for the research and study of global anthropogenic climate change.

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

# Base Station
This machine communicates with the AUV using radio communication. Its main role is selecting and beginning missions for the AUV. It also receives data wirelessly from the AUV and outputs to an in-house Python GUI.

## Hardware:
    Any Unix-like Machine (preferebly Ubuntu 16.04LTS+)
    A 915 MHz Radio (required)
    Xbox 360 Controller (optional)
    GPS device compatible with gpsd (optional)

## System Dependencies:
    python3-tk (for use with tkinter UI development)
    python3-pip (enable pip package manager)
    xboxdrv (Xbox Controller Driver)
    gpsd
    gpsd-clients (for the cgps program, optional)

## Python Packages (in requirements.txt):
    tkinter
    matplotlib
    pyserial
    gps3
    screeninfo
    autopep8 (optional)

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
    Python 3.5+ with pip
    gpsd
    gpsd-clients
    IMU Library/Drivers
    and many more...
This will continue to be updated as development continues.

## Python Packages (in requirements.txt):
    pyserial
    adafruit-circuitpython-bno055 (our Inertial Measurement Unit)
    and many more...
    
# Missions
The Nautilus AUV is designed to perform a wide variety of aquatic "missions", many of which involve the research and development of:

  * Underwater acoustic processing (acoustic)
  * Autonomous underwater navigation
  * Sonar echolocation 

# Development
Most development takes place at the MESOM Laboratory in the Scripps Institution of Oceanography at the University of California, San Diego. Due to the COVID-19 pandemic, software development will continue remotely for the forseeable future.

# Contributors
Pranav Mehta,
Software Lead 2023-2024

Yashil Vora,
Junior Software Lead 2023-2024

Girish Krishnan,
Software Lead 2022-2023

Deepta Bhardwaj,
Junior Software Lead 2022-2023

George Wu,
Software Development

Abirami Sabbani,
Software Development Lead 2021-2022
* Math - Computer Science
* UCSD Graduation: 2022

Stephen Boussarov,
Software Team Advisor
* Computer Science
* UCSD Graduation: 2022

Eric Estabaya,
Software Development
* Computer Science
* UCSD Graduation: 2022

Clair Ma,
Software Development
* Computer Science - Bioinformatics
* UCSD Graduation: 2023

Kevin Medzorian,
Former Software Team Lead
* Computer Science
* UCSD Graduation: 2021

Sean Chen,
Software Development
* Mathematics - Computer Science
* UCSD Graduation: 2024

Christopher Hughes,
Software Development
* Computer Engineering
* UCSD Graduation: 2024

Aleksa Stamenkovic,
Software Development
* Computer Science
* UCSD Graduation: 2023
