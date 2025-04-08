@echo off

REM Startup the main base_station file, using -B to prevent bytecode.
REM Note: the  ||  symbol means that if the previous command failed, do the next command.
REM command: startup.cmd

REM old code that ran the gui twice: python3 -B base_station.py || python -B base_station.py

REM new code:
python3 -B base_station.py