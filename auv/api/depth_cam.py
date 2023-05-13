import pyrealsense2 as rs
import numpy as np
import cv2 as cv
import time
import torch

# This is a pre-trained object detection model
# This will give a UserWarning when run, but that can be ignored
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
thresh = 7500


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
        except Exception as err:
            print("No RealSense camera found. Please connect a RealSense camera and try again.")
            return str(err)

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

    def detect_obstacles_depth(self, threshold):
        """
        Detect obstacles in the RealSenseCamera object's frameset
        Method: using depth map to find the average depth of pixels in each third of the image (split vertically)
        and identify which third has obsacles in it
        """

        # Get depth map
        depth_image = np.asanyarray(self.aligned_depth_frame.get_data())
        depth_image = cv.rotate(depth_image, cv.ROTATE_90_CLOCKWISE)

        # Split depth map into thirds
        third = int(depth_image.shape[1] / 3)
        left = depth_image[:, :third]
        middle = depth_image[:, third:third * 2]
        right = depth_image[:, third * 2:]

        # Find average depth of each third
        left_avg = np.average(left)
        middle_avg = np.average(middle)
        right_avg = np.average(right)

        # If a third has a signiicantly lower average depth than the other two, there is an obstacle in that third
        # TODO: modify this code and fine-tune it to work better
        # TEST IT ON REAL DATA AND OBSTACLES!!!
        if left_avg < threshold and left_avg < middle_avg and left_avg < right_avg:
            return "left"
        elif middle_avg < threshold and middle_avg < left_avg and middle_avg < right_avg:
            return "middle"
        elif right_avg < threshold and right_avg < left_avg and right_avg < middle_avg:
            return "right"
        else:
            return "none"

    def detect_obstacles_yolo(self):
        """
        Detect obstacles in the RealSenseCamera object's current frameset
        Method: using YOLOv5 object detection to find the number of obstacles in the image
        """
        # Get color image
        color_image = np.asanyarray(self.color_frame.get_data())

        # Detect objects in image
        results = model(color_image)

        # Return list of names of detected objects
        return results.names
        # TODO: make this method more useful to detect different kinds of obstacles

    def save_current_frames(self):
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

    def record_video(self, seconds):
        """
        Record a video using the RealSenseCamera object
        """

        # Use OpenCV to write video
        fourcc = cv.VideoWriter_fourcc(*'XVID')
        out = cv.VideoWriter('./Camera_Data/' + self.serial_number + '/sample_videos/video.avi', fourcc, 20.0, (640, 480))

        # Record video for specified number of seconds
        start_time = time.time()
        while (time.time() - start_time) < seconds:
            frames = self.get_frames()
            self.process_frames(frames)
            color_image = np.asanyarray(self.color_frame.get_data())
            out.write(color_image)

        # Release video
        out.release()

    def get_serial_number(self):
        """
        :return: The serial number of the RealSenseCamera object
        """
        return self.serial_number

    def stop(self):
        """
        Stop the RealSenseCamera object's pipeline
        """
        self.pipeline.stop()


if __name__ == "__main__":
    camera = RealSenseCamera()
    # Continuous while loop to get data from frames, show data in cv2 window
    try:
        while True:
            frames = camera.get_frames()
            camera.process_frames(frames)
            color = np.asanyarray(camera.raw_color_frame.get_data())
            color = cv.rotate(color, cv.ROTATE_90_CLOCKWISE)
            cv.imshow("Color",color)
            depth_image = np.asanyarray(camera.aligned_depth_frame.get_data())
            depth_image = cv.rotate(depth_image, cv.ROTATE_90_CLOCKWISE)
            depth_colormap = cv.applyColorMap(cv.convertScaleAbs(depth_image, alpha=0.03), cv.COLORMAP_JET)
            cv.imshow("Depth",depth_colormap)
            #print("Average depth map:", np.mean(depth_image))
            print(camera.detect_obstacles_depth(threshold=thresh))
            key = cv.waitKey(1)
            if key == ord('q'):
                break
    
    except KeyboardInterrupt:
        camera.stop()
        cv.destroyAllWindows()
