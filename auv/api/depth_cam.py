import numpy as np
import cv2
import pyrealsense2 as rs

# Configure depth stream
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

# Start streaming
pipeline.start(config)

# Create color map
color_map = cv2.COLORMAP_JET

try:
    while True:
        # Wait for a coherent pair of frames: depth and color
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()

        # Convert depth data to a numpy array
        depth_image = np.asanyarray(depth_frame.get_data())

        # Apply color map to depth data
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), color_map)

        # Display the depth data
        cv2.imshow('Depth', depth_colormap)

        # Wait for key press
        key = cv2.waitKey(1)
        if key == 27:  # ESC
            break

finally:
    # Stop streaming
    pipeline.stop()

    # Close all windows
    cv2.destroyAllWindows()
