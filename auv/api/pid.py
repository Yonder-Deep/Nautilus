from __future__ import print_function
import time

PITCH_CONTROL_TOLERANCE = 4.0
PITCH_TARGET_TOLERANCE = 2.0


class PID:
    """PID Controller"""

    def __init__(self, motor_controller, target, control_tolerance, target_tolerance, debug, name="", p=0.2, i=0.0, d=0.0, i_windup=20.0):
        # Initialize parameters
        self.name = name
        self.mc = motor_controller
        self.set_point = target
        self.control_tolerance = control_tolerance
        self.target_tolerance = target_tolerance
        self.p = p
        self.i = i
        self.d = d
        self.windup = i_windup
        self.is_debug = debug
        self.last_error = 0.0
        self.sum_error = 0.0
        self.last_time = time.time()
        self.within_tolerance = False

    def pid_heading(self, current_value):
        """PID Calculation"""
        # Calculate error
        #error = self.set_point - current_value
        abs_error = self.set_point - current_value
        if(abs_error < 180):
            error = abs_error
        else:
            error = abs_error - 360

        # Figure out state
        if(self.within_tolerance and abs(error) > self.control_tolerance):
            self.within_tolerance = False
        elif(not self.within_tolerance and abs(error) < self.target_tolerance):
            self.within_tolerance = True

        # PID
        if(self.within_tolerance):
            if(self.is_debug):
                #print("PID inside tolerance")
                print('[PID]In Target %7.2f Current %7.2f Error %7.2f' % (self.set_point, current_value, error), end='\r')

            return 0

        dt = time.time() - self.last_time

        # Calculate P term
        p_term = self.p * error
        # Calculate I term
        self.sum_error += error * (time.time() - self.last_time)
        i_change = self.sum_error if abs(self.sum_error) < self.windup else (
            self.windup if self.sum_error >= 0 else -self.windup)
        i_change *= dt
        i_term = self.i * i_change
        # Calculate D term
        d_term = self.d * (error - self.last_error)
        d_term /= dt

        # Update values for next iteration
        self.last_time = time.time()
        self.last_error = error
        if(self.is_debug):
            print('[PID]SetPoint %7.2f Current %7.2f Error %7.2f P %7.2f I %7.2f D %7.2f Feedback %7.2f' %
                  (self.set_point, current_value, error, p_term, i_term, d_term, p_term+i_term+d_term), end='\t')
        return p_term + i_term + d_term  # pid

    def pid(self, current_value):
        """PID Calculation"""
        # Calculate error
        error = self.set_point - current_value
        # Figure out state

        if(self.within_tolerance and abs(error) > self.control_tolerance):
            print("Not within tolerance")
            self.within_tolerance = False
        elif(not self.within_tolerance and abs(error) < self.target_tolerance):
            print("Within tolerance")
            self.within_tolerance = True

        # PID
        if(self.within_tolerance):
            if(self.is_debug):
                #print("PID inside tolerance")
                print('[PID %s] In Target %7.2f Current %7.2f Error %7.2f' % (self.name, self.set_point, current_value, error), end='\n')

            return 0

        dt = time.time() - self.last_time

        # Calculate P term
        p_term = self.p * error
        # Calculate I term
        self.sum_error += error * (time.time() - self.last_time)
        i_change = self.sum_error if abs(self.sum_error) < self.windup else (
            self.windup if self.sum_error >= 0 else -self.windup)
        i_change *= dt
        i_term = self.i * i_change
        # Calculate D term
        d_term = self.d * (error - self.last_error)
        d_term /= dt

        # Update values for next iteration
        self.last_time = time.time()
        self.last_error = error
        if(self.is_debug):
            print('[PID %s] SetPoint %7.2f Current %7.2f Error %7.2f P %7.2f I %7.2f D %7.2f Feedback %7.2f' %
                  (self.name, self.set_point, current_value, error, p_term, i_term, d_term, p_term+i_term+d_term), end='\n')
        return p_term + i_term + d_term

    def set_p(self, p):
        self.p = p

    def set_i(self, i):
        self.i = i

    def set_d(self, d):
        self.d = d

    def set_windup(self, windup):
        """Integral windup, also known as integrator windup or reset windup,
        refers to the situation in a PID feedback controller where
        a large change in setpoint occurs (say a positive change)
        and the integral terms accumulates a significant error
        during the rise (windup), thus overshooting and continuing
        to increase as this accumulated error is unwound
        (offset by errors in the other direction).
        The specific problem is the excess overshooting.
        """
        self.windup = windup

    def update_target(self, target):
        self.set_point = target
