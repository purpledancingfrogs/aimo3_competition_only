import re
from fractions import Fraction

def solve_geometry(p: str):
    p = p.lower()

    # area of rectangle
    m = re.search(r"rectangle.*?sides?\s*(\d+)\s*and\s*(\d+)", p)
    if m:
        a, b = int(m[1]), int(m[2])
        return a * b

    # area of square
    m = re.search(r"square.*?side\s*(\d+)", p)
    if m:
        s = int(m[1])
        return s * s

    # perimeter of square
    m = re.search(r"perimeter.*square.*side\s*(\d+)", p)
    if m:
        s = int(m[1])
        return 4 * s

    # circle area with integer radius (π ignored per contest style)
    m = re.search(r"circle.*radius\s*(\d+)", p)
    if m:
        r = int(m[1])
        return r * r

    return None
