import re
from fractions import Fraction

try:
    from sympy import isprime, factorint
except Exception:
    isprime = None
    factorint = None


class NTSolver:
    def _normalize(self, s: str) -> str:
        t = (s or "").lower()

        # strip latex / markup noise
        t = t.replace("$", " ")
        t = t.replace("{", " ").replace("}", " ")
        t = t.replace("\\,", " ").replace("\\;", " ").replace("\\:", " ")
        t = t.replace("\\cdot", " times ")
        t = t.replace("\\times", " times ")
        t = t.replace("×", " times ")

        # normalize unicode minus
        t = t.replace("−", "-")

        # collapse whitespace
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def _safe_eval_int_arith(self, t: str):
        # ONLY allow "int op int" with + - * /
        m = re.search(r'(?<![\w.])(-?\d+)\s*([+\-*/])\s*(-?\d+)(?![\w.])', t)
        if not m:
            return None
        a = int(m.group(1))
        op = m.group(2)
        b = int(m.group(3))
        try:
            if op == "+": return a + b
            if op == "-": return a - b
            if op == "*": return a * b
            if op == "/":
                if b == 0: return None
                frac = Fraction(a, b)
                return int(frac) if frac.denominator == 1 else float(frac)
        except Exception:
            return None
        return None

    def _solve_linear_for_x(self, t: str):
        # Accept forms like:
        # "solve 4+x=4 for x", "solve x+4=4", "solve 4-x=4", "solve 4=4+x", "solve 2x+3=11"
        # Convert implicit multiplication "2x" -> "2*x"
        tt = re.sub(r'(?<![\w.])(-?\d+)\s*x(?![\w.])', r'\1*x', t)

        if "solve" not in tt or "for x" not in tt:
            # still allow if equation contains x and '='
            if "x" not in tt or "=" not in tt:
                return None

        m = re.search(r'([-+*/x\d\s\.]+)\s*=\s*([-+*/x\d\s\.]+)', tt)
        if not m:
            return None

        left = m.group(1).strip()
        right = m.group(2).strip()

        def parse_side(expr: str):
            # linear-only: ax + b
            expr = expr.replace(" ", "")
            expr = expr.replace("-", "+-")
            parts = [p for p in expr.split("+") if p != ""]
            a = Fraction(0, 1)
            b = Fraction(0, 1)
            for p in parts:
                if "x" in p:
                    if p == "x": coef = Fraction(1, 1)
                    elif p == "-x": coef = Fraction(-1, 1)
                    else:
                        pm = re.fullmatch(r'(-?\d+)\*x', p)
                        if not pm:
                            return None
                        coef = Fraction(int(pm.group(1)), 1)
                    a += coef
                else:
                    if not re.fullmatch(r'-?\d+', p):
                        return None
                    b += Fraction(int(p), 1)
            return a, b

        L = parse_side(left)
        R = parse_side(right)
        if L is None or R is None:
            return None

        aL, bL = L
        aR, bR = R
        a = aL - aR
        b = bR - bL  # a*x = b

        if a == 0:
            return None

        x = b / a
        return int(x) if x.denominator == 1 else str(x)

    def solve(self, problem_text):
        t = self._normalize(problem_text)

        # direct arithmetic
        r = self._safe_eval_int_arith(t)
        if r is not None:
            return r

        # multiplication phrasing
        nums = re.findall(r'-?\d+', t)
        if "times" in t and len(nums) >= 2:
            try:
                return int(nums[0]) * int(nums[1])
            except Exception:
                pass

        # solve linear equation for x
        r = self._solve_linear_for_x(t)
        if r is not None:
            return r

        # primality
        if "prime" in t and nums and isprime is not None:
            try:
                return int(isprime(int(nums[0])))
            except Exception:
                pass

        # factorization
        if "factor" in t and nums and factorint is not None:
            try:
                return factorint(int(nums[0]))
            except Exception:
                pass

        return None
