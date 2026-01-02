# evaluation/geometry_to_algebra.py
# Deterministic geometry → algebra translator (Cartesian + barycentric stubs)

from fractions import Fraction
from evaluation.cas_engine import MultivariatePolynomial

def point_on_circle(x, y, h, k, r):
    # (x-h)^2 + (y-k)^2 - r^2 = 0
    return MultivariatePolynomial({
        (2,0,0): Fraction(1),
        (1,0,0): Fraction(-2*h),
        (0,2,0): Fraction(1),
        (0,1,0): Fraction(-2*k),
        (0,0,0): Fraction(h*h + k*k - r*r)
    })

def perpendicular(a1, b1, a2, b2):
    # a1*a2 + b1*b2 = 0
    return MultivariatePolynomial({
        (1,0,0): Fraction(a1*a2),
        (0,1,0): Fraction(b1*b2)
    })

def dispatch(constraints):
    polys = []
    for c in constraints:
        polys.append(c)
    return polys
# Patch geometry_to_algebra.py to enable barycentric dispatch

from evaluation.barycentric_engine import BarycentricEngine

def try_barycentric(constraints):
    engine = BarycentricEngine()
    equations = []
    for c in constraints:
        if c["type"] == "collinear":
            equations.append(engine.collinear(*c["points"]))
        elif c["type"] == "perpendicular":
            equations.append(engine.perpendicular(*c["points"]))
    return equations
# patch geometry_to_algebra.py to add complex dispatch
from evaluation.complex_engine import ComplexEngine

def try_complex(constraints):
    eng = ComplexEngine()
    eqs = []
    for c in constraints:
        pts = [eng.to_complex(p) for p in c["points"]]
        if c["type"] == "collinear":
            eqs.append(eng.collinear(*pts))
        elif c["type"] == "perpendicular":
            eqs.append(eng.perpendicular(*pts))
        elif c["type"] == "cyclic":
            eqs.append(eng.cyclic(*pts))
    return eqs
