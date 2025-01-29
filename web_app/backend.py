class Backend():
    def test_motor(self, motor, speed=10, duration=10):
        """Attempts to send the AUV a signal to test a given motor."""

    def test_heading(self, target):
        """Attempts to send the AUV a signal to test heading PID."""
    
    def test_imu_calibration(self):
        return

    def abort_mission(self):
        """Attempts to abort the mission for the AUV."""

    def start_mission(self, mission, depth, t):
        """Attempts to start a mission and send to AUV."""

    def send_halt(self):
        return

    def send_calibrate_depth(self):
        return

    def send_calibrate_heading(self):
        return

    def send_abort(self):
        return
    
    def send_dive(self, depth):
        return

    def send_pid_update(self, axis, p_constant, i_constant, d_constant):
        return

    def mission_started(self, index):
        """When AUV sends mission started, switch to mission mode"""
        return