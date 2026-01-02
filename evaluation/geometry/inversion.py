from fractions import Fraction
from collections import namedtuple

Point = namedtuple("Point", ["x", "y"])
Circle = namedtuple("Circle", ["center", "radius_sq"])
Line = namedtuple("Line", ["a", "b", "c"])

class InversionMapper:
    def __init__(self, center: Point, radius_sq: Fraction):
        self.O = center
        self.r2 = radius_sq

    def invert_point(self, p: Point) -> Point:
        dx = p.x - self.O.x
        dy = p.y - self.O.y
        d2 = dx*dx + dy*dy
        if d2 == 0:
            raise ValueError("Inversion center has no finite image")
        f = self.r2 / d2
        return Point(self.O.x + f*dx, self.O.y + f*dy)

    def invert_circle(self, c: Circle):
        dx = c.center.x - self.O.x
        dy = c.center.y - self.O.y
        d2 = dx*dx + dy*dy

        if d2 == c.radius_sq:
            a = 2*dx
            b = 2*dy
            c_val = -(a*self.O.x + b*self.O.y + self.r2)
            return Line(a, b, c_val)

        denom = d2 - c.radius_sq
        f = self.r2 / denom
        new_center = Point(self.O.x + f*dx, self.O.y + f*dy)
        new_radius_sq = (self.r2*self.r2*c.radius_sq)/(denom*denom)
        return Circle(new_center, new_radius_sq)

    def invert_line(self, l: Line):
        num = l.a*self.O.x + l.b*self.O.y + l.c
        if num == 0:
            return l
        norm_sq = l.a*l.a + l.b*l.b
        f = self.r2 / (2*num)
        new_center = Point(self.O.x + f*l.a, self.O.y + f*l.b)
        new_radius_sq = (self.r2*self.r2*norm_sq)/(4*num*num)
        return Circle(new_center, new_radius_sq)
