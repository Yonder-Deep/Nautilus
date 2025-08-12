import numpy as np

# Tried adding individual class
class GpsCoordinate:
    def __init__(self, lat, lon, alt):
        self.lat = lat
        self.lon = lon
        self.alt = alt

class GpsVelocity:
    def __init__(self, vN, vE, vD):
        self.vN = vN
        self.vE = vE
        self.vD = vD

class ImuData:
    def __init__(self, accX, accY, accZ):
        self.accX = accX
        self.accY = accY
        self.accZ = accZ


SIG_W_A = 0.05
SIG_A_D = 0.01
TAU_A = 100.0
SIG_GPS_P_NE = 3.0
SIG_GPS_P_D = 6.0 
SIG_GPS_V_NE = 0.5
SIG_GPS_V_D = 1.0
P_P_INIT = 10.0 
P_V_INIT = 1.0
P_AB_INIT = 0.9810
G = 9.807
ECC2 = 0.0066943799901
EARTH_RADIUS = 6378137.0


class EKF:
    def __init__(self):
        self.initialized_ = False

        # Initial States
        self.vn_ins = 0.0
        self.ve_ins = 0.0
        self.vd_ins = 0.0
        self.V_ins = np.zeros(3, dtype=np.float64)

        self.lat_ins = 0.0
        self.lon_ins = 0.0
        self.alt_ins= 0.0
        self.lla_ins: np.ndarray = np.zeros(3, dtype=np.float64)

        self.abx = 0.0
        self.aby = 0.0
        self.abz = 0.0
        self.accel_bias = np.zeros(3, dtype=np.float32)

        self.P = np.zeros((9, 9), dtype=np.float32)
        self.R = np.zeros((6, 6), dtype=np.float32)
        self.H = np.zeros((6, 9), dtype=np.float32)
        self.Rw = np.zeros((6, 6), dtype=np.float32)

        self.f_b = np.zeros(3, dtype=np.float32)
        self.grav = np.array([0.0, 0.0, G], dtype=np.float32)

        self._initialize_matrices()

    def _initialize_matrices(self):
        self.H[0:3, 0:3] = np.identity(3, dtype=np.float32)
        self.H[3:6, 3:6] = np.identity(3, dtype=np.float32)

        self.Rw[0:3, 0:3] = (SIG_W_A**2.0) * np.identity(3)
        self.Rw[3:6, 3:6] = (2.0 * SIG_A_D*SIG_A_D / TAU_A) * np.identity(3)

        self.R[0:2, 0:2] = (SIG_GPS_P_NE*SIG_GPS_P_NE) * np.identity(2)
        self.R[2, 2] = SIG_GPS_P_D*SIG_GPS_P_D
        self.R[3:5, 3:5] = (SIG_GPS_V_NE*SIG_GPS_V_NE) * np.identity(2)
        self.R[5, 5] = SIG_GPS_V_D*SIG_GPS_V_D

    def initialized(self) -> bool:
        return self.initialized_

    def get_latitude_rad(self): return self.lat_ins
    def get_longitude_rad(self): return self.lon_ins
    # Altitude is basically 0 here...
    def get_altitude_m(self): return self.alt_ins
    def get_vel_north_ms(self): return self.vn_ins
    def get_vel_east_ms(self): return self.ve_ins
    # Velocity down is also 0 here since we used Course Made Good for direction...
    def get_vel_down_ms(self): return self.vd_ins

    # Helper Functions
    def _earth_radius(self, lat):
        sin_lat_sq = np.sin(lat)**2.0
        denom = abs(1.0 - ECC2 * sin_lat_sq)
        # Avoid division by zero or sqrt of negative if denom is exactly 0
        if denom < 1e-10:
             denom = 1e-10
        sqrt_denom = np.sqrt(denom)
        Rew = EARTH_RADIUS / sqrt_denom
        Rns = EARTH_RADIUS * (1.0 - ECC2) / (denom * sqrt_denom)
        return Rew, Rns

    def _llarate(self, V_ned, lat, alt):
        Rew, Rns = self._earth_radius(lat)
        lla_dot = np.zeros(3, dtype=np.float64)
        vn, ve, vd = V_ned
        
        # Protect against division by zero or invalid latitude
        cos_lat = np.cos(lat)
        if abs(cos_lat) < 1e-8: # Avoid division by zero near poles
            cos_lat = 1e-8 * np.sign(cos_lat) if cos_lat != 0 else 1e-8
        
        h_Rns = Rns + alt
        h_Rew = Rew + alt
        
        if h_Rns < 1e-3: h_Rns = 1e-3
        if h_Rew < 1e-3: h_Rew = 1e-3

        lla_dot[0] = vn / h_Rns
        lla_dot[1] = ve / (h_Rew * cos_lat)
        lla_dot[2] = -vd 
        return lla_dot

    def _lla2ecef(self, lla):
        """LLA (Lat, Long, Atitude) to ECEF coordinates."""
        lat, lon, alt = lla
        Rew, _ = self._earth_radius(lat)
        ecef = np.zeros(3, dtype=np.float64)
        cos_lat = np.cos(lat)
        sin_lat = np.sin(lat)
        cos_lon = np.cos(lon)
        sin_lon = np.sin(lon)

        N_plus_h = Rew + alt
        ecef[0] = N_plus_h * cos_lat * cos_lon
        ecef[1] = N_plus_h * cos_lat * sin_lon
        ecef[2] = (Rew * (1.0 - ECC2) + alt) * sin_lat
        return ecef

    def _ecef2ned(self, ecef_vec, ref_lla):
        lat_ref, lon_ref, _ = ref_lla
        sin_lat = np.sin(lat_ref)
        cos_lat = np.cos(lat_ref)
        sin_lon = np.sin(lon_ref)
        cos_lon = np.cos(lon_ref)

        # Rotation matrix from ECEF to NED
        R_ecef2ned = np.array([
            [-sin_lat * cos_lon, -sin_lat * sin_lon,  cos_lat],
            [-sin_lon,            cos_lon,           0],
            [-cos_lat * cos_lon, -cos_lat * sin_lon, -sin_lat]
        ], dtype=np.float64)

        ned = R_ecef2ned @ ecef_vec
        return ned
    
    def _quat2dcm(self, q):
        """Converts quaternion (w, x, y, z) to a DCM"""
        q0, q1, q2, q3 = q
        q0_2 = q0**2; q1_2 = q1**2; q2_2 = q2**2; q3_2 = q3**2
        q1q2 = q1*q2; q0q3 = q0*q3
        q1q3 = q1*q3; q0q2 = q0*q2
        q2q3 = q2*q3; q0q1 = q0*q1

        dcm = np.zeros((3, 3), dtype=np.float32)
        
        # Check with textbook if this Quaternion -> DCM is correct 
        dcm[0,0] = q0_2 + q1_2 - q2_2 - q3_2
    
        dcm[0,0] = 2.0 * q0_2 - 1.0 + 2.0 * q1_2
        dcm[1,1] = 2.0 * q0_2 - 1.0 + 2.0 * q2_2
        dcm[2,2] = 2.0 * q0_2 - 1.0 + 2.0 * q3_2

        dcm[0,1] = 2.0 * q1q2 + 2.0 * q0q3
        dcm[0,2] = 2.0 * q1q3 - 2.0 * q0q2

        dcm[1,0] = 2.0 * q1q2 - 2.0 * q0q3
        dcm[1,2] = 2.0 * q2q3 + 2.0 * q0q1

        dcm[2,0] = 2.0 * q1q3 + 2.0 * q0q2
        dcm[2,1] = 2.0 * q2q3 - 2.0 * q0q1
        return dcm

    # --- Actual EKF ---
    def initialize(self, init_gps_vel, init_gps_coor):
        """Initializes the EKF states and covariance."""
        self.lat_ins, self.lon_ins, self.alt_ins = init_gps_coor.lat, init_gps_coor.lon, init_gps_coor.alt
        self.vn_ins, self.ve_ins, self.vd_ins = init_gps_vel.vN, init_gps_vel.vE, init_gps_vel.vD
        self.lla_ins[:] = [self.lat_ins, self.lon_ins, self.alt_ins]
        self.V_ins[:] = [self.vn_ins, self.ve_ins, self.vd_ins]

        self.abx, self.aby, self.abz = 0.0, 0.0, 0.0
        self.accel_bias[:] = [self.abx, self.aby, self.abz]

        self.P = np.zeros((9, 9), dtype=np.float32)
        self.P[0:3, 0:3] = (P_P_INIT**2.0) * np.identity(3)
        self.P[3:6, 3:6] = (P_V_INIT**2.0) * np.identity(3)
        self.P[6:9, 6:9] = (P_AB_INIT**2.0) * np.identity(3)

        self.initialized_ = True
        print("Position/Velocity Initialized")


    def predict(self, dt, imu_data, q):
        C_N2B = self._quat2dcm(q)
        C_B2N = C_N2B.T

        acc_raw = np.array([imu_data.accX, imu_data.accY, imu_data.accZ], dtype=np.float32)
        self.f_b = acc_raw - self.accel_bias

        print(C_B2N @ self.f_b)
        accel_nav = C_B2N @ self.f_b + self.grav

        self.vn_ins += accel_nav[0] * dt
        self.ve_ins += accel_nav[1] * dt
        self.vd_ins += accel_nav[2] * dt
        self.V_ins[:] = [self.vn_ins, self.ve_ins, self.vd_ins]

        lla_dot = self._llarate(self.V_ins, self.lat_ins, self.alt_ins)
        self.lat_ins += lla_dot[0] * dt
        self.lon_ins += lla_dot[1] * dt
        self.alt_ins += lla_dot[2] * dt
        self.lla_ins[:] = [self.lat_ins, self.lon_ins, self.alt_ins]

        # Calculate Jacobian Fs (9x9) - relates error state derivative to error state
        Fs = np.zeros((9, 9), dtype=np.float32)
        Fs[0:3, 3:6] = np.identity(3)
        Fs[5, 2] = 2.0 * G / EARTH_RADIUS
        Fs[3:6, 6:9] = -C_B2N
        Fs[6:9, 6:9] = (-1.0 / TAU_A) * np.identity(3)
        PHI = np.identity(9, dtype=np.float32) + Fs * dt

        Gs = np.zeros((9, 6), dtype=np.float32)
        Gs[3:6, 0:3] = -C_B2N
        Gs[6:9, 3:6] = np.identity(3)
        Q = PHI @ Gs @ self.Rw @ Gs.T * dt
        Q = 0.5 * (Q + Q.T)
        
        self.P = PHI @ self.P @ PHI.T + Q
        self.P = 0.5 * (self.P + self.P.T)
        self.P += np.identity(9) * 1e-12


    def correct(self, gps_vel, gps_coord):
        if not self.initialized_:
            print("Initialize First")
            return

        lla_gps = np.array([gps_coord.lat, gps_coord.lon, gps_coord.alt], dtype=np.float64)
        pos_ecef_ins = self._lla2ecef(self.lla_ins)
        pos_ecef_gps = self._lla2ecef(lla_gps)
        pos_err_ned = self._ecef2ned(pos_ecef_gps - pos_ecef_ins, self.lla_ins)

        # Measurement innovation vector y (6x1)
        y = np.zeros(6, dtype=np.float32)
        y[0:3] = pos_err_ned.astype(np.float32)
        y[3] = gps_vel.vN - self.vn_ins
        y[4] = gps_vel.vE - self.ve_ins
        y[5] = gps_vel.vD - self.vd_ins

        P = self.P 
        H = self.H
        R = self.R

        PHt = P @ H.T
        S = H @ PHt + R

        # Could use solve_kalman_gain() helper from unscented but this seems to work
        S_inv = np.linalg.inv(S)
        K = PHt @ S_inv
        x_err = K @ y

        dpn, dpe, dpd = x_err[0], x_err[1], x_err[2]
        dvn, dve, dvd = x_err[3], x_err[4], x_err[5]
        dabx, daby, dabz = x_err[6], x_err[7], x_err[8]

        Rew, Rns = self._earth_radius(self.lat_ins)
        h_plus_Rns = Rns + self.alt_ins
        h_plus_Rew = Rew + self.alt_ins
        cos_lat = np.cos(self.lat_ins)
        if h_plus_Rns < 1e-3: 
            h_plus_Rns = 1e-3
        if abs(cos_lat) < 1e-8: 
            cos_lat = 1e-8 * np.sign(cos_lat) if cos_lat != 0 else 1e-8
        if h_plus_Rew < 1e-3: 
            h_plus_Rew = 1e-3

        self.lat_ins += dpn / h_plus_Rns
        self.lon_ins += dpe / (h_plus_Rew * cos_lat)
        self.alt_ins -= dpd

        self.vn_ins += dvn
        self.ve_ins += dve
        self.vd_ins += dvd

        self.abx += dabx
        self.aby += daby
        self.abz += dabz

        self.lla_ins[:] = [self.lat_ins, self.lon_ins, self.alt_ins]
        self.V_ins[:] = [self.vn_ins, self.ve_ins, self.vd_ins]
        self.accel_bias[:] = [self.abx, self.aby, self.abz]


        I_KH = np.identity(9, dtype=np.float32) - K @ H
        # Used Joseph form for better numerical stability
        P_corrected = I_KH @ P @ I_KH.T + K @ R @ K.T

        self.P = P_corrected
        self.P = 0.5 * (self.P + self.P.T)
        self.P += np.identity(9) * 1e-12
