import math

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.rx = 0
        self.ry = 0
        self.rz = 0
        self.focal_lenght = 200

    def position(self):
        return self.x, self.y, self.z

    def rotation(self):
        return math.radians(self.rx), math.radians(self.ry), math.radians(self.rz)


