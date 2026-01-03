import sys
import re
from math import sqrt
import sympy as sp

class Solver:
    def solve(self, text: str):
        text = (text or "").strip().lower()

        # ---- sequences / geometry command prefixes (these may contain "=" as params) ----
        if text.startswith("ap term"):
            return self.solve_ap(text)
        if text.startswith("gp term"):
            return self.solve_gp(text)
        if text.startswith("sequence"):
            return self.solve_sequence(text)

        if text.startswith("distance"):
            return self.solve_distance(text)
        if text.startswith("midpoint"):
            return self.solve_midpoint(text)
        if text.startswith("similar_triangles"):
            return self.solve_similar_triangles(text)

        # ---- inequalities ----
        if "<=" in text or ">=" in text or "<" in text or ">" in text:
            if any(op in text for op in ["<=", ">=", "<", ">"]):
                # avoid treating coordinate tuples as inequalities
                if not text.startswith(("distance", "midpoint")):
                    return self.solve_inequality(text)

        # ---- equations (true algebra only) ----
        if self.is_equation(text):
            return self.solve_equation(text)

        # ---- arithmetic ----
        return self.solve_arithmetic(text)

    def is_equation(self, text: str) -> bool:
        return ("=" in text) and (text.count("=") == 1) and (not text.startswith(("ap", "gp", "sequence", "similar_triangles")))

    # ---------------- EQUATIONS / INEQUALITIES ----------------

    def solve_equation(self, text: str):
        # supports: 2*x + 3 = 11, 3*x-5=16, x+y=5 (no crash; returns dict or param form)
        lhs, rhs = [s.strip() for s in text.split("=", 1)]

        # normalize caret for powers
        lhs = lhs.replace("^", "**")
        rhs = rhs.replace("^", "**")

        # detect variables
        vars_found = sorted(set(re.findall(r"\b[a-z]\b", lhs + " " + rhs)))
        if not vars_found:
            # numeric equation: return 1 if true else 0
            try:
                return int(sp.simplify(sp.sympify(lhs) - sp.sympify(rhs)) == 0)
            except Exception:
                return 0

        sym_vars = sp.symbols(" ".join(vars_found), real=True)
        sym_map = {str(v): v for v in sym_vars} if isinstance(sym_vars, tuple) else {vars_found[0]: sym_vars}

        try:
            expr = sp.sympify(lhs, locals=sym_map) - sp.sympify(rhs, locals=sym_map)
        except Exception:
            return "PARSE_ERROR"

        try:
            if len(vars_found) == 1:
                v = sym_map[vars_found[0]]
                sol = sp.solve(expr, v, dict=True)
                if not sol:
                    return "NO_SOLUTION"
                val = sol[0].get(v, None)
                if val is None:
                    return "NO_SOLUTION"
                val = sp.simplify(val)
                if val.is_Integer:
                    return int(val)
                if val.is_Rational:
                    return f"{int(val.p)}/{int(val.q)}"
                return str(val)
            else:
                # under/overdetermined possible; return one param-free solution if exists, else relation
                sol = sp.linsolve([expr], list(sym_map.values()))
                if sol is None or len(sol) == 0:
                    return "NO_SOLUTION"
                s = next(iter(sol))
                # if parameters present, return tuple form
                return str(s)
        except Exception:
            return "SOLVE_ERROR"

    def solve_inequality(self, text: str):
        # supports: 3*x - 7 <= 8, x^2 - 1 >= 0
        t = text.replace("^", "**").replace("≤", "<=").replace("≥", ">=")
        # choose operator (prefer <= >=)
        op = None
        for cand in ["<=", ">=", "<", ">"]:
            if cand in t:
                op = cand
                break
        if op is None:
            return "PARSE_ERROR"
        left, right = [s.strip() for s in t.split(op, 1)]

        vars_found = sorted(set(re.findall(r"\b[a-z]\b", left + " " + right)))
        if not vars_found:
            return "PARSE_ERROR"
        v = sp.Symbol(vars_found[0], real=True)

        try:
            L = sp.sympify(left, locals={vars_found[0]: v})
            R = sp.sympify(right, locals={vars_found[0]: v})
        except Exception:
            return "PARSE_ERROR"

        rel = {"<=": sp.Le(L, R), ">=": sp.Ge(L, R), "<": sp.Lt(L, R), ">": sp.Gt(L, R)}[op]
        try:
            s = sp.solve_univariate_inequality(rel, v, relational=False)
            return str(s)
        except Exception:
            return "SOLVE_ERROR"

    # ---------------- GEOMETRY ----------------

    def solve_distance(self, text: str):
        nums = list(map(float, re.findall(r"-?\d+(?:\.\d+)?", text)))
        if len(nums) != 4:
            return "PARSE_ERROR"
        x1, y1, x2, y2 = nums
        return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def solve_midpoint(self, text: str):
        nums = list(map(float, re.findall(r"-?\d+(?:\.\d+)?", text)))
        if len(nums) != 4:
            return "PARSE_ERROR"
        x1, y1, x2, y2 = nums
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def solve_similar_triangles(self, text: str):
        ratio = re.search(r"ratio=(\d+):(\d+)", text)
        small = re.search(r"small=(\d+)", text)
        if not ratio or not small:
            return "PARSE_ERROR"
        a, b = int(ratio.group(1)), int(ratio.group(2))
        s = int(small.group(1))
        # corresponding side = s * (b/a)
        val = sp.Rational(s * b, a)
        return int(val) if val.is_Integer else f"{int(val.p)}/{int(val.q)}"

    # ---------------- SEQUENCES ----------------

    def solve_sequence(self, text: str):
        nums = list(map(int, re.findall(r"-?\d+", text)))
        if len(nums) < 3:
            return "PARSE_ERROR"
        d = nums[1] - nums[0]
        if all(nums[i+1] - nums[i] == d for i in range(len(nums)-1)):
            return nums[-1] + d
        # fallback: return last term (no crash)
        return nums[-1]

    def solve_ap(self, text: str):
        n = int(re.search(r"n=(\d+)", text).group(1))
        a = int(re.search(r"a=(\d+)", text).group(1))
        d = int(re.search(r"d=(\d+)", text).group(1))
        return a + (n - 1) * d

    def solve_gp(self, text: str):
        n = int(re.search(r"n=(\d+)", text).group(1))
        a = int(re.search(r"a=(\d+)", text).group(1))
        r = int(re.search(r"r=(\d+)", text).group(1))
        return a * (r ** (n - 1))

    # ---------------- ARITHMETIC ----------------

    def solve_arithmetic(self, text: str):
        t = text.replace("^", "**")
        t = re.sub(r"[^0-9\.\+\-\*\/\(\)\s]", "", t)
        try:
            v = sp.N(sp.sympify(t))
            if v.is_Integer:
                return int(v)
            return float(v)
        except Exception:
            return "PARSE_ERROR"

if __name__ == "__main__":
    print(Solver().solve(sys.stdin.read()))
