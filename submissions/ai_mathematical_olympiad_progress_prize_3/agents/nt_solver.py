import re
from fractions import Fraction

class NTSolver:
    def __init__(self):
        pass

    def _normalize(self, text):
        if not text:
            return ""
        text = re.sub(r'\\\(|\\\)|\\\[|\\\]|\$', '', text)
        text = re.sub(r'Solve\s+|for\s+x\.?|What\s+is\s+', '', text, flags=re.IGNORECASE)
        text = text.replace('\\times', '*').replace('\\cdot', '*')
        text = text.replace('\u2212', '-')
        text = text.replace('^', '**')
        return "".join(text.split())

    def _solve_linear(self, expr):
        try:
            if '=' not in expr:
                return int(eval(expr, {"__builtins__": None}, {}))

            lhs, rhs = expr.split('=')
            rhs_val = Fraction(eval(rhs, {"__builtins__": None}, {}))

            m = re.match(r'([+-]?\d*)\*?x([+-]\d+)?', lhs)
            if not m:
                m = re.match(r'([+-]\d+)([+-]?\d*)\*?x', lhs)
                if not m:
                    return None
                b_raw, a_raw = m.groups()
            else:
                a_raw, b_raw = m.groups()

            if a_raw in (None, "", "+"):
                a = Fraction(1)
            elif a_raw == "-":
                a = Fraction(-1)
            else:
                a = Fraction(a_raw)

            b = Fraction(b_raw) if b_raw else Fraction(0)

            x = (rhs_val - b) / a
            return int(x) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"
        except Exception:
            return None

    def solve(self, problem):
        if isinstance(problem, str) and problem.endswith(".csv"):
            return 0
        clean = self._normalize(problem)
        out = self._solve_linear(clean)
        return out if out is not None else 0
