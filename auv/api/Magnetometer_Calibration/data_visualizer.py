"""
data_visualizer.py

This file provides a way to visualize both raw and corrected sensor data with 
an interactive 3D scatter plot.
"""

import pandas as pd
import matplotlib.pyplot as plt

# Load data with error handling
try:
    df = pd.read_csv("raw_mag_data/mag_raw.csv", names=["x", "y", "z"])
except FileNotFoundError:
    print("Error: mag_raw.csv not found!")
    exit()

# Create figure and 3D axis
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Plot data
ax.scatter(df["x"], df["y"], df["z"], c=df["z"], cmap="viridis", edgecolor="k", alpha=0.8)

# Labels and title
ax.set_title("3D Data Visualization", fontsize=14)
ax.set_xlabel("X-Axis")
ax.set_ylabel("Y-Axis")
ax.set_zlabel("Z-Axis")

# Show plot
plt.show()