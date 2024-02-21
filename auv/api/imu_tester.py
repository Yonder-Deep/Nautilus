from Adafruit_BNO055 import BNO055
import logging
import sys
import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(14, GPIO.IN)


# bno = BNO055.BNO055(serial_port="/dev/ttyAMA0", rst=8)
bno = BNO055.BNO055()

if len(sys.argv) == 2 and sys.argv[1].lower() == '-v':
    logging.basicConfig(level=logging.DEBUG)

error_count = 0

while error_count < 20:
    try:
        begun = bno.begin()
        break
    except:
        print("BNO didn't initialize. Retrying...")
        error_count += 1
        time.sleep(0.2)

if error_count == 20:
    raise RuntimeError("Failed to initialize BNO055! Is the sensor connected?")

status, self_test, error = bno.get_system_status()
print('System status: {0}'.format(status))
print('Self test result (0x0F is normal): 0x{0:02X}'.format(self_test))
# Print out an error if system status is in error mode.
if status == 0x01:
    print('System error: {0}'.format(error))
    print('See datasheet section 4.3.59 for the meaning.')

# Print BNO055 software revision and other diagnostic data.
sw, bl, accel, mag, gyro = bno.get_revision()
print('Software version:   {0}'.format(sw))
print('Bootloader version: {0}'.format(bl))
print('Accelerometer ID:   0x{0:02X}'.format(accel))
print('Magnetometer ID:    0x{0:02X}'.format(mag))
print('Gyroscope ID:       0x{0:02X}\n'.format(gyro))

print('Reading BNO055 data, press Ctrl-C to quit...')
while True:
    # Read the Euler angles for heading, roll, pitch (all in degrees).
    bno.set_axis_remap(1, 0, 2, 1, 0, 0) 

    heading, roll, pitch = bno.read_euler()
    roll = -1 * roll
    pitch = -1 * pitch 
    # Read the calibration status, 0=uncalibrated and 3=fully calibrated.
    sys, gyro, accel, mag = bno.get_calibration_status()

    x, y, z, x_sign, y_sign, z_sign = bno.get_axis_remap(); 
    # Print everything out.

    print(x, y, z, x_sign, y_sign, z_sign); 
    print('Heading={0:0.2F} Roll={1:0.2F} Pitch={2:0.2F}\tSys_cal={3} Gyro_cal={4} Accel_cal={5} Mag_cal={6}'.format(
          heading, roll, pitch, sys, gyro, accel, mag))
    # Other values you can optionally read:
    # Orientation as a quaternion:
    #x,y,z,w = bno.read_quaterion()
    # Sensor temperature in degrees Celsius:
    #temp_c = bno.read_temp()
    # Magnetometer data (in micro-Teslas):
    #x,y,z = bno.read_magnetometer()
    # Gyroscope data (in degrees per second):
    #x,y,z = bno.read_gyroscope()
    # Accelerometer data (in meters per second squared):
    #x,y,z = bno.read_accelerometer()
    # Linear acceleration data (i.e. acceleration from movement, not gravity--
    # returned in meters per second squared):
    #x,y,z = bno.read_linear_acceleration()
    # Gravity acceleration data (i.e. acceleration just from gravity--returned
    # in meters per second squared):
    #x,y,z = bno.read_gravity()
    # Sleep for a second until the next reading.
    time.sleep(1)