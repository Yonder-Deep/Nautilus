
class MockController():
    def __init__(self):
        self.position = [0, 0]
        self.velocity = [0, 0]
        self.acceleration = [0, 0]
        self.heading = 0
        self.heading_vel = 0
        self.heading_accel = 0

    def input(self, input=tuple):
        