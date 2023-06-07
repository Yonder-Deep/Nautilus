import pandas as pd
from datetime import datetime

# Initialize empty lists to store the data
time_list = []
heading_list = []
roll_list = []
pitch_list = []
acceleration_x_list = []
acceleration_y_list = []
acceleration_z_list = []
linear_acceleration_x_list = []
linear_acceleration_y_list = []
linear_acceleration_z_list = []

# Open the text file and read the data
with open('imu_data.txt', 'r') as file:

    for line in file:
        if line.strip():
            # Extract the initial time
            if 'Time' in line:
                initial_time = next(file).strip()
                break

    print(initial_time)
    # Convert this date and time to a datetime object
    initial_time = datetime.strptime(initial_time, '%Y-%m-%d %H:%M:%S.%f')
    file.close()

with open('imu_data.txt', 'r') as file:

    for line in file:
        if line.strip():
            # Extract the values and append them to the relevant lists
            if 'Time' in line:
                time = next(file).strip()
                # Convert the time to a datetime object
                time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
                # Subtract the initial time from the current time
                time = time - initial_time

                # Convert the datetime object to seconds
                time = time.total_seconds()
                time_list.append(time)
            elif 'Heading' in line:
                heading = float(next(file).strip())
                heading_list.append(heading)
            elif 'Roll' in line:
                roll = float(next(file).strip())
                roll_list.append(roll)
            elif 'Pitch' in line:
                pitch = float(next(file).strip())
                pitch_list.append(pitch)
            elif 'Acceleration' in line:
                acceleration = next(file).strip()
                acceleration = acceleration.split(',')
                acceleration_x = float(acceleration[0])
                acceleration_y = float(acceleration[1])
                acceleration_z = float(acceleration[2])
                acceleration_x_list.append(acceleration_x)
                acceleration_y_list.append(acceleration_y)
                acceleration_z_list.append(acceleration_z)

            elif 'Linear acceleration' in line:
                linear_acceleration = next(file).strip()
                linear_acceleration = linear_acceleration.split(',')
                linear_acceleration_x = float(linear_acceleration[0])
                linear_acceleration_y = float(linear_acceleration[1])
                linear_acceleration_z = float(linear_acceleration[2])
                linear_acceleration_x_list.append(linear_acceleration_x)
                linear_acceleration_y_list.append(linear_acceleration_y)
                linear_acceleration_z_list.append(linear_acceleration_z)


# Create a list of dictionaries containing the extracted data
data = []
for i in range(len(time_list)):
    data.append({
        'Time': time_list[i],
        'Heading': heading_list[i],
        'Roll': roll_list[i],
        'Pitch': pitch_list[i],
        'Acceleration_x': acceleration_x_list[i],
        'Acceleration_y': acceleration_y_list[i],
        'Acceleration_z': acceleration_z_list[i],
        'Linear_acceleration_x': linear_acceleration_x_list[i],
        'Linear_acceleration_y': linear_acceleration_y_list[i],
        'Linear_acceleration_z': linear_acceleration_z_list[i]

    })

# Create a DataFrame from the list of dictionaries
df = pd.DataFrame(data)

# Save the DataFrame as a .csv file
df.to_csv('imu_data.csv', index=False)
