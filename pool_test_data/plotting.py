import matplotlib.pyplot as plt
import numpy as np

# Import data csv
data = np.genfromtxt('imu_data.csv', delimiter=',', names=True)

# Plot data time vs acceleration
plt.plot(data['Time'], data['Acceleration_x'], label='Acceleration x')
plt.plot(data['Time'], data['Acceleration_y'], label='Acceleration y')
plt.plot(data['Time'], data['Acceleration_z'], label='Acceleration z')
plt.xlabel('Time (s)')
plt.ylabel('Acceleration (m/s^2)')
plt.title('Acceleration vs Time')
plt.legend()
plt.show()

# Plot data time vs linear acceleration
plt.plot(data['Time'], data['Linear_acceleration_x'], label='Linear acceleration x')
plt.plot(data['Time'], data['Linear_acceleration_y'], label='Linear acceleration y')
plt.plot(data['Time'], data['Linear_acceleration_z'], label='Linear acceleration z')
plt.xlabel('Time (s)')
plt.ylabel('Linear acceleration (m/s^2)')
plt.title('Linear acceleration vs Time')
plt.legend()
plt.show()

# Plot data time vs heading
plt.plot(data['Time'], data['Heading'], label='Heading')
plt.xlabel('Time (s)')
plt.ylabel('Heading (degrees)')
plt.title('Heading vs Time')
plt.legend()
plt.show()

# Plot data time vs roll
plt.plot(data['Time'], data['Roll'], label='Roll')
plt.xlabel('Time (s)')
plt.ylabel('Roll (degrees)')
plt.title('Roll vs Time')
plt.legend()
plt.show()

# Plot data time vs pitch
plt.plot(data['Time'], data['Pitch'], label='Pitch')
plt.xlabel('Time (s)')
plt.ylabel('Pitch (degrees)')
plt.title('Pitch vs Time')
plt.legend()
plt.show()
