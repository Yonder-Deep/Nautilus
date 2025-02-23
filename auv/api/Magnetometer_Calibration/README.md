# Magnetometer Calibration

## Overview
This provides tools for calibrating a magnetometer using an IMU 
connected via I2C. The calibration process consists of two steps: raw data 
collection and offset calculation.

## Requirements
- IMU with a magnetometer (connected via I2C)
- Python 3+
- GCC (for compiling `offset_calculator`)

# Magnetometer Calibration Steps

## Step 1: Collect Raw Magnetometer Data
Connect your IMU to your system via I2C and run the calibration script:
```bash
python3 magnetometer_calibration.py
```

## Step 2: Calculate Magnetometer Offset
Compile the offset_calculator program
```bash
gcc offset_calculator.c -o offset_calculator -lm
```
Run the compiled program
```bash
./offset_calculator
```

When prompted, enter the filename: **mag_raw.csv**

Use **1000** for Hm when prompted.

The program will compute calibration offsets and output correction data 
code, which can then be incorporated into the source code of your program.


