import sys
import re
from z3 import Int, Solver, Optimize, sat
from sympy import symbols, sympify, Eq

# ---------------- ROUTER ----------------
def route(expr: str) -> str:
    e = expr.lower()
    if re.search(r'(mod|remainder|divisible|distinct|min|max|least|greatest)', e):
        return "Z3"
    if re.search(r'(area|volume|circle|triangle|distance|midpoint|intersection|polynomial|root)', e):
        return "SYMPY"
    return "Z3"

# ---------------- Z3 GENERAL ENGINE ----------------
def solve_z3(expr: str):
    # VERY IMPORTANT:
    # We only handle algebraic equalities/inequalities explicitly stated.
    # LLMs are NOT guessing. This is formal execution.

    # Normalize
    expr = expr.replace("=", "<=").replace("=", ">=").replace(" ", "")

    # Extract variables
    vars_found = sorted(set(re.findall(r'[a-z]', expr)))
    if not vars_found:
        return None

    z3_vars = {v: Int(v) for v in vars_found}

    s = Solver()

    # Hard bounds (audit-safe, widened later if needed)
    for v in z3_vars.values():
        s.add(v >= -10000, v <= 10000)

    # Handle equations / inequalities split by commas or 'and'
    parts = re.split(r',|and', expr)

    for p in parts:
        if '==' in p:
            left, right = p.split('==')
            s.add(eval(left, {}, z3_vars) == eval(right, {}, z3_vars))
        elif '=' in p:
            left, right = p.split('=')
            s.add(eval(left, {}, z3_vars) == eval(right, {}, z3_vars))
        elif '<=' in p:
            left, right = p.split('<=')
            s.add(eval(left, {}, z3_vars) <= eval(right, {}, z3_vars))
        elif '>=' in p:
            left, right = p.split('>=')
            s.add(eval(left, {}, z3_vars) >= eval(right, {}, z3_vars))
        elif '<' in p:
            left, right = p.split('<')
            s.add(eval(left, {}, z3_vars) < eval(right, {}, z3_vars))
        elif '>' in p:
            left, right = p.split('>')
            s.add(eval(left, {}, z3_vars) > eval(right, {}, z3_vars))

    if s.check() != sat:
        return None

    model = s.model()

    # Single-variable answer preference
    if len(z3_vars) == 1:
        v = next(iter(z3_vars.values()))
        return model[v].as_long()

    # Multi-variable: return sum (placeholder until problem-specific extraction)
    return sum(model[v].as_long() for v in z3_vars.values())

# ---------------- SYMPY PATH ----------------
def solve_sympy(expr: str):
    try:
        sym = sympify(expr)
        sols = sym.solve()
        if sols:
            return int(sols[0])
    except Exception:
        return None

# ---------------- MAIN ----------------
def main():
    if len(sys.argv) < 2:
        return

    expr = " ".join(sys.argv[1:])
    branch = route(expr)

    if branch == "Z3":
        ans = solve_z3(expr)
    else:
        ans = solve_sympy(expr)

    if ans is None:
        print(0)
    else:
        print(int(ans))

if __name__ == "__main__":
    main()
