![Yonder Deep Logo](https://github.com/Yonder-Deep/Nautilus/blob/Control-System/logo.png)
# Nautilus
Repository for [YonderDeep's](https://www.yonderdeep.org/) Nautilus AUV software.

## Basics
The codebase is split among two machines: 
  * A base station (a Windows / macOS / Linux machine)
  * Nautilus (an AUV with a Raspberry Pi 3 or similar running Raspbian)
The base station and Nautilus can communicate over *any* IP interface. That IP interface may be established via a serial port with `ppp`, normal Wi-Fi, Ethernet, Wi-Fi HaLow, or other methods.

## Installing and Running
System dependencies are simply:
    * python3/pip (on both auv and base station)
    * nodejs/nvm/npm (only on base station)
For video streaming (not required), `gstreamer` is required.
Further instructions are in subordinate READMEs in `auv/` and `web_app/`.

## Recent Contributors
Yanis Herne,
Software Lead
* Biophysics - Molecular Biology

Logan Wong,
Software Development
* Computer Engineering

Sofina Fei,
Software Development
* Computer Science

Abijit Jayachandran
Former Software Lead
* Computer Engineering

Pranav Mehta
Former Software Lead
* Computer Engineering

## Former Contributors

Abirami Sabbani,
Software Development Lead
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
