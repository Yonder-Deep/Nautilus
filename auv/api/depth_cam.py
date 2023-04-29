import pyrealsense2 as rs
import numpy as np
import cv2 as cv

class RealSenseCamera:
    """
    
    Initialize a RealSenseCamera object with the following attributes:
    :param serial_number: The serial number of the RealSense camera
    
    """

    def __init__(self) -> None:
        # Query all existing RealSense cameras connected to the computer and get the serial number of the first cam found

        # INITIALIZE CAMERA
        try:
            ctx = rs.context()
            devices = ctx.query_devices()
            serial_number = devices[0].get_info(rs.camera_info.serial_number)

            # Create RealSense D415 camera object and pipeline
            self.serial_number = serial_number
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            self.config.enable_device(serial_number)
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 60)
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 60)
            self.config.enable_stream(rs.stream.infrared, 640, 480, rs.format.y8, 60)

            # Start streaming
            self.pipeline.start(self.config)

            # Enable IR emitter and set max laser power
            self.profile = self.pipeline.get_active_profile()
            self.depth_sensor = self.profile.get_device().first_depth_sensor()
            self.depth_sensor.set_option(rs.option.emitter_enabled, 1)
            #self.depth_sensor.set_option(rs.option.enable_auto_exposure, 1)
            #self.depth_sensor.set_option(rs.option.enable_auto_white_balance, 1)
            #self.depth_sensor.set_option(rs.option.output_trigger_enabled, 1)
            self.depth_sensor.set_option(rs.option.laser_power, 360)
            self.depth_sensor.set_option(rs.option.global_time_enabled, 1)
        except:
            print("No RealSense camera found. Please connect a RealSense camera and try again.")
            exit()

    def get_frames(self):
        """
        :return: The frameset of the RealSenseCamera object
        """
        return self.pipeline.wait_for_frames()
        
    def process_frames(self, frames):
        """
        
        :param frames: The frameset of the RealSenseCamera object

        """    
        aligned_frames = rs.align(rs.stream.depth).process(frames)

        # Get aligned frames
        self.aligned_depth_frame = aligned_frames.get_depth_frame()  # aligned_depth_frame is a 640x480 depth image
        self.aligned_depth_frame = rs.decimation_filter(1).process(self.aligned_depth_frame)
        self.aligned_depth_frame = rs.disparity_transform(True).process(self.aligned_depth_frame)
        self.aligned_depth_frame = rs.spatial_filter().process(self.aligned_depth_frame)
        self.aligned_depth_frame = rs.temporal_filter().process(self.aligned_depth_frame)
        self.aligned_depth_frame = rs.disparity_transform(False).process(self.aligned_depth_frame)

        self.color_frame = aligned_frames.get_color_frame()
        self.raw_color_frame = frames.get_color_frame()

    def detect_obstacles(self):
        """
        Detect obstacles in the RealSenseCamera object's frameset
        """
        # TODO: Implement obstacle detection

    def save_frames(self):
        """
        Save the frames of the RealSenseCamera object as .jpg and .npy files
        """
        # Convert images to numpy arrays
        depth_image = np.asanyarray(self.aligned_depth_frame.get_data())
        color_image = np.asanyarray(self.color_frame.get_data())
        raw_color_image = np.asanyarray(self.raw_color_frame.get_data())
        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        depth_colormap = cv.applyColorMap(cv.convertScaleAbs(depth_image, alpha=0.03), cv.COLORMAP_JET)

        # Save color as .jpg and depth as .npy
        cv.imwrite("./Camera_Data/" + self.serial_number + "/sample_images/image.jpg", color_image)
        cv.imwrite("./Camera_Data/" + self.serial_number + "/sample_images/raw_image.jpg", raw_color_image)
        np.save("./Camera_Data/" + self.serial_number + "/sample_images/depth_map.npy", depth_image)
        cv.imwrite("./Camera_Data/" + self.serial_number + "/sample_images/depth.png", depth_colormap)

if __name__ == "__main__":
    camera = RealSenseCamera()
    frames = camera.get_frames()
    camera.process_frames(frames)

