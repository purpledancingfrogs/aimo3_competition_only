# evaluation/complex_engine.py
# Deterministic complex-plane geometry engine (audit-safe, stdlib only)

from fractions import Fraction
import cmath

class ComplexEngine:
    def __init__(self):
        pass

    def to_complex(self, p):
        x, y = p
        return complex(Fraction(x), Fraction(y))

    def collinear(self, a, b, c):
        # (b-a)/(c-a) is real
        if a == c:
            return False
        z = (b - a) / (c - a)
        return z.imag == 0

    def perpendicular(self, a, b, c, d):
        # (b-a) ⟂ (d-c)  ⇔  (b-a)/(d-c) is purely imaginary
        if d == c:
            return False
        z = (b - a) / (d - c)
        return z.real == 0

    def cyclic(self, a, b, c, d):
        # cross ratio real
        if (a-b)*(c-d) == 0:
            return False
        z = (a-b)*(c-d)/((b-c)*(d-a))
        return z.imag == 0
