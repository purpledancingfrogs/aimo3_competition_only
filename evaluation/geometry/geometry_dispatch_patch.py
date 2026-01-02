from evaluation.geometry.inversion import InversionMapper, Point, Circle, Line
from fractions import Fraction

def maybe_apply_inversion(objects, anchor_point):
    circles = [o for o in objects if isinstance(o, Circle)]
    if len(circles) < 2:
        return objects

    # Deterministic anchor: first circle center
    O = anchor_point if anchor_point else circles[0].center
    r2 = Fraction(1)

    inv = InversionMapper(O, r2)
    transformed = []

    for o in objects:
        if isinstance(o, Circle):
            transformed.append(inv.invert_circle(o))
        elif isinstance(o, Line):
            transformed.append(inv.invert_line(o))
        elif isinstance(o, Point):
            transformed.append(inv.invert_point(o))
        else:
            transformed.append(o)

    # Accept inversion only if it strictly reduces circle count
    if sum(isinstance(x, Circle) for x in transformed) < len(circles):
        return transformed

    return objects
