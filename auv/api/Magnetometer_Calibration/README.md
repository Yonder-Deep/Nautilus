# Magnetometer Calibration

## Overview
This provides tools for calibrating a magnetometer using an IMU 
connected via I2C. The calibration process consists of two steps: raw data 
collection and offset calculation, as well as data visualization if needed.

## Requirements
- IMU with a magnetometer (connected via I2C)
- Python 3+
- Matplotlib and Pandas

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

When prompted, enter the filename: **mag_raw.csv**.
Use **1000** for Hm when prompted.

The program will compute calibration offsets and output correction data 
code, which can then be incorporated into the source code of your program.

## Step 3: Visualize sensor data if needed
Make sure **mag_raw.csv** exists in this directory. Then run:
```bash
python3 data_visualizer.py
```

