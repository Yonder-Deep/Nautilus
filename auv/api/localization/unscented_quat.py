"""
unscented_quaternion.py

An Unscented Kalman Filter that uses quaternions
________________________________________________________________________________
q0 - the reference or mean quaternion that represents the center of the chart
q - quaternion representing the current orientation~real component first
e - a point on the chart that represents the current orientation relative to q0
w - angular velocity
P - orientation covariance matrix
Qw - angular velocity process noise
Qa - acceleration process noise
Rw - angular velocity measurement noise
Ra - acceleration measurement noise
W0 - weight for the mean sigma values
State Vector = [e, w, Qw, Qa]
________________________________________________________________________________
TODO
-Optimize (Use numpy whenever possible, modify objects in-place (use x[:]=))
-Add position tracking with GPS and motor input signal (Bu term in literature)
"""

from math import sqrt, sin, cos

import numpy as np
from scipy.linalg import cholesky, solve_triangular


class MUKF:
    def __init__(self):
        # Make sure to tune process and measurement noise
        self.q0 = np.array([1.0, 0.0, 0.0, 0.0])
        self.q = np.array([1.0, 0.0, 0.0, 0.0])
        self.e = np.zeros(3)
        self.w = np.full(3, 1e-10)
        self.P = np.eye(6) * 0.1
        self.Qw = np.eye(3) * 0.1
        self.Qa = np.eye(3) * 0.1
        self.Qm = np.eye(3) * 0.1
        self.Rw = np.eye(3) * 0.01
        self.Ra = np.eye(3) * 0.01
        self.Rm = np.eye(3) * 0.01
        self.W0 = 1.0/25.0
        self.chartUpdate = True

    def set_q(self, qIn):
        """ Manually set the current quaternion orientation """
        self.q = qIn
        self.q0 = qIn
        self.e = np.zeros(3)

    def reset_orientation(self):
        """ Manually reset the current quaternion orientation """
        self.q0 = np.array([1.0, 0.0, 0.0, 0.0])
        self.q = np.array([1.0, 0.0, 0.0, 0.0])
        self.e = np.zeros(3)

    def get_current_orientation(self):
        """ Gets the current quaternion orientation """
        return self.q

    def update_imu(self, am, wm, mm, dt):
        """
        Takes in acceleration (m/s), angular velocity (rad/s), magnetic field 
        strength (T), and delta time to repeatedly update the estimated state
        """
        Pe = np.zeros((15, 15))
        Pe[0:6, 0:6] = self.P
        Pe[6:9, 6:9] = self.Qw
        Pe[9:12, 9:12] = self.Qa
        Pe[12:15, 12:15] = self.Qm

        L_pe_upper = cholesky(Pe)
        Pe_L = L_pe_upper.T
        Pe[:] = Pe_L
        Wi = (1.0 - self.W0) / (2.0 * 12)
        alpha = 1.0 / sqrt(2.0 * Wi)
        Pe *= alpha        
        
        X = np.zeros((31, 16))
        Y = np.zeros((31, 9))

        X[0, :4] = self.q
        X[0, 4:7] = self.w
        X[0, 7:16] = 0.0

        # if not self.chartUpdate:
        #     self.q0[:] = self.q
        #     self.e[:] = 0.0

        for j in range(15):
            eP_plus = self.e + Pe[:, j][0:3]
            X[j+1, :4] = MUKF.chart_to_manifold(self.q0, eP_plus)
            X[j+1, 4:7] = self.w + Pe[:, j][3:6]
            X[j+1, 7:16] = Pe[:, j][6:15]

        for j in range(15):
            eP_minus = self.e - Pe[:, j][0:3]
            X[j+13, :4] = MUKF.chart_to_manifold(self.q0, eP_minus)
            X[j+13, 4:7] = self.w - Pe[:, j][3:6]
            X[j+13, 7:16] = -Pe[:, j][6:15]

        for j in range(31):
            MUKF.state_transition(X[j], dt)
            prod = X[0, :4] @ X[j, :4]
            if prod < 0.0:
                X[j, :4] *= -1.0
            MUKF.state_to_measurement(Y[j], X[j])

        xmean = np.zeros(7)
        ymean = np.zeros(9)
        xmean[:7] = self.W0*X[0, :7]
        ymean[:9] = self.W0*Y[0, :9]
        for j in range(1, 31):
            xmean[:7] += Wi*X[j, :7]
            ymean[:9] += Wi*Y[j, :9]

        qmeanNorm = np.linalg.norm(xmean[:4])
        xmean[:4] /= qmeanNorm
        
        Pxx = np.zeros((6, 6))
        Pxy = np.zeros((6, 9))
        Pyy = np.zeros((9, 9))
        dX = np.zeros(6)
        dY = np.zeros(9)

        dX[:3] = MUKF.manifold_to_chart(xmean[:4], X[0, :4])
        dX[3:6] = X[0, 4:7] - xmean[4:7]
        dY[:] = Y[0, :9] - ymean[:9]

        Pxx += self.W0 * np.outer(dX, dX)
        Pxy += self.W0 * np.outer(dX, dY)
        Pyy += self.W0 * np.outer(dY, dY)

        for k in range(1, 25):
            dX[:3] = MUKF.manifold_to_chart(xmean[:4], X[k, :4])
            dX[3:6] = X[k, 4:7] - xmean[4:7]
            dY[:] = Y[k, :9] - ymean[:9]
            Pxx += Wi * np.outer(dX, dX)
            Pxy += Wi * np.outer(dX, dY)
            Pyy += Wi * np.outer(dY, dY)

        Pyy[0:3, 0:3] += self.Ra
        Pyy[3:6, 3:6] += self.Rw
        Pyy[6:9, 6:9] += self.Rm

        K = MUKF.solve_kalman_gain(np.copy(Pyy), Pxy)
        anorm = np.linalg.norm(am)
        mnorm = np.linalg.norm(mm)
        y = np.concatenate(((am) / anorm - ymean[:3],
                            (wm) - ymean[3:6],
                            (mm) / mnorm - ymean[6:]))
        dx = K @ y

        self.q0 = xmean[:4]
        self.e = dx[:3]
        self.q = MUKF.chart_to_manifold(np.copy(self.q0), np.copy(self.e))
        self.q /= np.linalg.norm(self.q)
        self.w = xmean[4:7] + dx[3:6]
        self.P = Pxx - K @ Pyy @ K.T 
        self.P = 0.5 * (self.P + self.P.T)
    
    def manifold_to_chart(qm, q):
        """ Maps the quaternion q to the qm-centered orthographic chart """
        delta = np.zeros(4)
        delta[0] = qm[0]*q[0] + qm[1]*q[1] + qm[2]*q[2] + qm[3]*q[3]
        delta[1] = qm[0]*q[1] - q[0]*qm[1] - qm[2]*q[3] + qm[3]*q[2]
        delta[2] = qm[0]*q[2] - q[0]*qm[2] - qm[3]*q[1] + qm[1]*q[3]
        delta[3] = qm[0]*q[3] - q[0]*qm[3] - qm[1]*q[2] + qm[2]*q[1]

        if delta[0] < 0.0:
            delta *= -1.0

        e = np.zeros(3)
        e[0] = 2.0 * delta[1]
        e[1] = 2.0 * delta[2]
        e[2] = 2.0 * delta[3]
        return e

    def chart_to_manifold(qm, e):
        """ Maps the point e in the qm-centered chart to the manifold """
        enorm = np.linalg.norm(e)
        if enorm > 2.0:
            aux = 2.0 / enorm
            e *= aux
            enorm = 2.0

        delta = np.zeros(4)
        delta[0] = sqrt(1.0 - 0.25 * enorm * enorm)
        delta[1:4] = 0.5 * e

        q = np.zeros(4)
        q[0] = qm[0]*delta[0] - qm[1]*delta[1] - qm[2]*delta[2] - qm[3]*delta[3]
        q[1] = qm[0]*delta[1] + delta[0]*qm[1] + qm[2]*delta[3] - qm[3]*delta[2]
        q[2] = qm[0]*delta[2] + delta[0]*qm[2] + qm[3]*delta[1] - qm[1]*delta[3]
        q[3] = qm[0]*delta[3] + delta[0]*qm[3] + qm[1]*delta[2] - qm[2]*delta[1]
        return q

    def state_transition(x, dt):
        """ Predicts next state from angular velocity and previous state """
        wp = x[4:7] + x[7:10] * dt
        wnorm = np.linalg.norm(wp)

        qw = np.zeros(4)
        if wnorm != 0.0:
            wdt05 = 0.5 * wnorm * dt
            qw[0] = cos(wdt05)
            qw[1:4] = wp * (sin(wdt05) / wnorm )
        else:
            qw[0] = 1.0
            qw[1:4] = 0.0

        qp = np.zeros(4)
        qp = np.zeros(4)
        qp[0] = x[0]*qw[0] - x[1]*qw[1] - x[2]*qw[2] - x[3]*qw[3]
        qp[1] = x[0]*qw[1] + qw[0]*x[1] + x[2]*qw[3] - x[3]*qw[2]
        qp[2] = x[0]*qw[2] + qw[0]*x[2] + x[3]*qw[1] - x[1]*qw[3]
        qp[3] = x[0]*qw[3] + qw[0]*x[3] + x[1]*qw[2] - x[2]*qw[1]

        x[:4] = qp
        x[4:7] = wp

    def state_to_measurement(y, x):
        """ Predicts IMU measurements given the state """
        RT = np.zeros((3, 3))
        RT[0, 0] = 1.0 - 2.0*(x[2]*x[2] + x[3]*x[3])
        RT[0, 1] = 2.0*(x[1]*x[2] - x[3]*x[0])
        RT[0, 2] = 2.0*(x[1]*x[3] + x[2]*x[0])

        RT[1, 0] = 2.0*(x[1]*x[2] + x[3]*x[0])
        RT[1, 1] = 1.0 - 2.0*(x[1]*x[1] + x[3]*x[3])
        RT[1, 2] = 2.0*(x[2]*x[3] - x[1]*x[0])

        RT[2, 0] = 2.0*(x[1]*x[3] - x[2]*x[0])
        RT[2, 1] = 2.0*(x[2]*x[3] + x[1]*x[0])
        RT[2, 2] = 1.0 - 2.0*(x[1]*x[1] + x[2]*x[2])

        ap = np.array([0, 0, 1])
        y[:3] = RT @ ap
        y[3:6] = x[4:7]
        mp = np.array([1, 0, 0])
        y[6:] = RT @ mp

    def solve_kalman_gain(S, M):
        """ Solves for K using Cholesky decomposition """
        L_upper = cholesky(S)
        L_lower = L_upper.T
        Y = solve_triangular(L_lower, M.T, lower=True)
        K = solve_triangular(L_upper, Y, lower=False)
        return K.T