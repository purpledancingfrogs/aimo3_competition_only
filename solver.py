import sys
import re
from z3 import Int, Solver, Optimize, sat

# ---------- ROUTER ----------
def route(expr: str) -> str:
    e = expr.lower()
    if re.search(r'(mod|remainder|divisible|integer|distinct|min|max|least|greatest)', e):
        return "Z3"
    if re.search(r'(polynomial|roots|derivative|integral|circle|triangle|area|volume|intersection)', e):
        return "SYMPY"
    if re.search(r'(process|iteration|nth step|repeat)', e):
        return "BRUTE"
    return "Z3"

# ---------- Z3 SAFE TEMPLATE ----------
def solve_z3(expr: str):
    # VERY FIRST CANONICAL FORM: single-variable linear / affine integer equations
    # This will be extended, not replaced.
    expr = expr.replace(" ", "")

    m = re.fullmatch(r'([+-]?\d*)\*?x([+-]\d+)?=([+-]?\d+)', expr)
    if not m:
        return None

    a, b, c = m.groups()

    if a in ("", "+"):
        a = 1
    elif a == "-":
        a = -1
    else:
        a = int(a)

    b = int(b) if b else 0
    c = int(c)

    x = Int("x")
    s = Solver()

    # Hard bounds (audit-safe)
    s.add(x >= -10000, x <= 10000)
    s.add(a * x + b == c)

    if s.check() != sat:
        return None

    return s.model()[x].as_long()

# ---------- MAIN ----------
def main():
    if len(sys.argv) > 1:
        expr = " ".join(sys.argv[1:])
    else:
        return

    branch = route(expr)

    if branch == "Z3":
        ans = solve_z3(expr)
        if ans is None:
            print(0)
        else:
            print(ans)
    else:
        print(0)

if __name__ == "__main__":
    main()
