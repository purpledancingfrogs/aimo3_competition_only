import re
from pathlib import Path

p = Path("solver.py")
t = p.read_text(encoding="utf-8")

if "def _try_linear_equation" in t:
    print("LINEAR_EXISTS")
    raise SystemExit(0)

marker = "\ndef solve(text: str)"
i = t.find(marker)
if i == -1:
    raise SystemExit("SOLVE_DEF_NOT_FOUND")

block = r'''
def _try_linear_equation(s: str) -> int | None:
    # Minimal deterministic linear solver for forms like: 2*x + 3 = 11 (returns integer if exact/int-floorable)
    m = re.search(r"([^=]{1,200})=([^=]{1,200})", s)
    if not m:
        return None
    left = _clean_text(m.group(1))
    right = _clean_text(m.group(2))
    if "x" not in left and "x" not in right:
        return None
    if "x" in right and "x" not in left:
        left, right = right, left

    # Sympy path if available
    if sp is not None:
        try:
            x = sp.Symbol("x")
            eq = sp.Eq(sp.sympify(left, locals={"x": x}), sp.sympify(right, locals={"x": x}))
            sol = sp.solve(eq, x)
            if sol:
                return _safe_int(sol[0])
        except Exception:
            pass

    # Fallback: parse left as a*x + b, right numeric
    try:
        expr = left.replace(" ", "")
        expr = expr.replace("-", "+-")
        terms = [tt for tt in expr.split("+") if tt]
        a = Fraction(0)
        b = Fraction(0)
        for tt in terms:
            if "x" in tt:
                coef = tt.replace("x", "")
                if coef in ("", "+"):
                    coef = "1"
                elif coef == "-":
                    coef = "-1"
                a += _safe_eval_expr(coef)
            else:
                b += _safe_eval_expr(tt)

        if a == 0:
            return None
        c = _safe_eval_expr(right)
        xval = (c - b) / a
        return _safe_int(xval)
    except Exception:
        return None
'''
t2 = t[:i] + block + t[i:]
p.write_text(t2, encoding="utf-8")
print("PATCH_OK")
