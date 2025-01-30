@echo off

REM Install all dependencies listed in requirements.txt
REM Note: the  ||  symbol means that if the previous command failed, do the next command.

echo Installing packages from requirements.txt...
python3 -m pip install -r requirements.txt || python -m pip install -r requirements.txt