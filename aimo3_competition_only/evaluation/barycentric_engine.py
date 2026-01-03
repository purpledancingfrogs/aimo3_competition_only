# evaluation/barycentric_engine.py
# Deterministic Barycentric Geometry Translator
# Standard Library ONLY

from fractions import Fraction

class BarycentricEngine:
    """
    Converts triangle geometry constraints into algebraic relations
    using barycentric coordinates.
    """

    def __init__(self, A=(0,0), B=(1,0), C=(0,1)):
        self.A = A
        self.B = B
        self.C = C

    def point(self, alpha, beta, gamma):
        s = alpha + beta + gamma
        if s == 0:
            raise ValueError("Invalid barycentric coordinates")
        alpha, beta, gamma = alpha/s, beta/s, gamma/s
        x = alpha*self.A[0] + beta*self.B[0] + gamma*self.C[0]
        y = alpha*self.A[1] + beta*self.B[1] + gamma*self.C[1]
        return (x, y)

    def collinear(self, p, q, r):
        (x1,y1),(x2,y2),(x3,y3)=p,q,r
        return (x2-x1)*(y3-y1)-(x3-x1)*(y2-y1) == 0

    def perpendicular(self, p, q, r, s):
        (x1,y1),(x2,y2),(x3,y3),(x4,y4)=p,q,r,s
        return (x2-x1)*(x4-x3)+(y2-y1)*(y4-y3) == 0

    def area_ratio(self, p, q, r):
        (x1,y1),(x2,y2),(x3,y3)=p,q,r
        return abs(x1*(y2-y3)+x2*(y3-y1)+x3*(y1-y2))

