from fractions import Fraction

class InversionEngine:
    # Inversion w.r.t. circle (O, R^2)
    # Maps point P to P' such that OP * OP' = R^2
    def invert_point(self, O, P, R2):
        (ox, oy) = O
        (px, py) = P
        dx = px - ox
        dy = py - oy
        denom = dx*dx + dy*dy
        if denom == 0:
            return None
        k = Fraction(R2, denom)
        return (ox + k*dx, oy + k*dy)

    # Line <-> Circle mapping under inversion
    def invert_line(self, O, line):
        # line: ax + by + c = 0
        # returns circle coefficients (deterministic symbolic form)
        (a,b,c) = line
        (ox,oy) = O
        # Standard symbolic inversion identity
        return (
            a*a + b*b,
            2*(a*c + a*a*ox + a*b*oy),
            2*(b*c + a*b*ox + b*b*oy),
            c*c + 2*c*(a*ox + b*oy)
        )
