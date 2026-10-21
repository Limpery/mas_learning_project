"""Точка и евклидово расстояние."""

import math
from dataclasses import dataclass


@dataclass
class Point:
    x: float
    y: float

    def __repr__(self):
        return f'({self.x:g}; {self.y:g})'

    def get_distance_to_other(self, other_point):
        return math.dist((self.x, self.y), (other_point.x, other_point.y))
