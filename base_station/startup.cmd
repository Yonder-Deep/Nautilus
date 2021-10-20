@echo off

REM Startup the main base_station file, using -B to prevent bytecode.
REM Note: the  ||  symbol means that if the previous command failed, do the next command.
REM command: startup.cmd
python3 -B base_station.py || python -B base_station.py
