import math


class Points:
    def __init__(self, coordinates):
        self.x = coordinates[0]
        self.y = coordinates[1]

    def __add__(self, increment):
        return Points((self.x + increment[0], self.y + increment[1]))

    def __sub__(self, increment):
        return Points((self.x - increment[0], self.y - increment[1]))

    def __repr__(self):
        return "({}, {})".format(self.x, self.y)

    def distance(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y-other.y)**2)

    def check_distance(self, other, max_value):
        return self.distance(other) < max_value

    def angle(self, other):
        sin = self.y - other.y
        cos = other.x - self.x
        return math.atan2(sin, cos)

    def to_tuple(self):
        return self.x, self.y
