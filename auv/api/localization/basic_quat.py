"""
basic_quaternion.py

Very basic kalman filter based on the quaternion kinematics equation. This 
filter treats nonlinear equations using the standard kalman process but 
tries to linearizes them using a first degree polynomial. It works though.
________________________________________________________________________________
q - quaternion representing the current orientation~real component first
P - orientation covariance matrix
H - state to measurement matrix
Q - process noise
R - measurement noise 
State Vector = [q]
________________________________________________________________________________
TODO
-Fix residual calculation, should multiply the inverse of the first quaternion 
by the second quaternion to find the difference not just subtract
"""
from math import atan2, sqrt, cos, sin
import numpy as np
from scipy.spatial.transform import Rotation

class MUKF:
    def __init__(self):
        # Make sure to tune process and measurement noise
        self.q = np.array([1, 0, 0, 0])
        self.P = np.eye(4) * 1
        self.H = np.eye(4) * 1
        self.Q = np.eye(4) * 1
        self.R = np.eye(4) * 1
        
    def get_current_orientation(self):
        """ Gets the current quaternion orientation """
        return self.q
    
    def update_imu(self, am, wm, mm, dt):
        """ 
        Takes in acceleration (m/s), angular velocity (rad/s), magnetic field 
        strength (T), and delta time to repeatedly update the estimated state
        """
        # State transition matrix
        omega = np.array([
            [0, -wm[0], -wm[1], -wm[2]],
            [wm[0], 0, wm[2], -wm[1]],
            [wm[1], -wm[2], 0, wm[0]],
            [wm[2], wm[1], -wm[0], 0]
        ])
        F = (np.eye(4) + dt * 0.5 * omega)

        # Predict state and covariance
        x_p = F @ self.x
        P_p = F @ self.P @ F.T + self.Q
        
        # Calculate measurement
        phi = atan2(am[1], am[2])
        theta = atan2(-am[0], sqrt(am[1] * am[1] + am[2] * am[2]))
        psi = atan2(mm[0] * cos(theta) + mm[1] * sin(phi) * sin(theta) + mm[2] * cos(phi) * sin(theta),
                    mm[1] * cos(phi) - mm[2] * sin(phi))
        z = Rotation.from_euler('ZYX', [psi, theta, phi]).as_quat()

        # Calculate residual
        y = (z - self.H @ x_p)

        # Kalman gain
        S = self.H @ P_p @ self.H.T + self.R
        K = P_p @ self.H.T @ np.linalg.inv(S)

        # Update state and covariance estimate
        self.x = x_p + K @ y
        self.P = (np.eye(4) - K @ self.H) @ P_p
