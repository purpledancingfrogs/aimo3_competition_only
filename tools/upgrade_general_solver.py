import re, ast, math
from fractions import Fraction

def _norm_text(s: str) -> str:
    if s is None:
        return ""
    s = s.replace("\r\n","\n").replace("\r","\n")
    s = s.replace("\u2212","-").replace("\u2013","-").replace("\u2014","-")
    s = s.replace("\u00a0"," ")
    return s

def _safe_eval_expr(expr: str):
    expr = _norm_text(expr).strip()
    expr = expr.replace("^","**")
    if len(expr) > 400:
        return None
    if re.search(r"[A-Za-z]", expr):
        return None
    try:
        node = ast.parse(expr, mode="eval")
    except Exception:
        return None

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant):
            if isinstance(n.value, (int, float)):
                if isinstance(n.value, float):
                    return Fraction(n.value).limit_denominator(10**6)
                return Fraction(n.value, 1)
            return None
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            v = ev(n.operand)
            if v is None: return None
            return v if isinstance(n.op, ast.UAdd) else -v
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)):
            a = ev(n.left); b = ev(n.right)
            if a is None or b is None: return None
            if isinstance(n.op, ast.Add): return a + b
            if isinstance(n.op, ast.Sub): return a - b
            if isinstance(n.op, ast.Mult): return a * b
            if isinstance(n.op, ast.Div):
                if b == 0: return None
                return a / b
            if isinstance(n.op, ast.FloorDiv):
                if b == 0: return None
                if a.denominator != 1 or b.denominator != 1: return None
                return Fraction(a.numerator // b.numerator, 1)
            if isinstance(n.op, ast.Mod):
                if b == 0: return None
                if a.denominator != 1 or b.denominator != 1: return None
                return Fraction(a.numerator % b.numerator, 1)
            if isinstance(n.op, ast.Pow):
                if b.denominator != 1: return None
                e = b.numerator
                if abs(e) > 50: return None
                if a.denominator != 1 and e < 0: return None
                if a.denominator != 1: return None
                return Fraction(pow(a.numerator, e), 1)
        return None

    return ev(node)

def _parse_linear_eq(prompt: str):
    # Matches forms like: 2*x + 3 = 11  or  3x - 5 = 16
    s = _norm_text(prompt)
    m = re.search(r'([\-]?\s*\d+)\s*\*?\s*x\s*([+\-]\s*\d+)?\s*=\s*([\-]?\s*\d+)', s, re.IGNORECASE)
    if not m:
        m = re.search(r'([\-]?\s*\d+)\s*x\s*([+\-]\s*\d+)?\s*=\s*([\-]?\s*\d+)', s, re.IGNORECASE)
    if not m:
        return None
    a = int(m.group(1).replace(" ",""))
    b = int(m.group(2).replace(" ","")) if m.group(2) else 0
    c = int(m.group(3).replace(" ",""))
    if a == 0:
        return None
    num = c - b
    if num % a != 0:
        return None
    return str(num // a)

def solve_general(prompt: str) -> str:
    s = _norm_text(prompt)

    # Fast path: explicit inline arithmetic like "Compute: ( ... )"
    m = re.search(r'(?:Compute|Evaluate|Find|Calculate)\s*:\s*([0-9\(\)\+\-\*/\^\s%\.]+)', s, re.IGNORECASE)
    if m:
        v = _safe_eval_expr(m.group(1))
        if isinstance(v, Fraction) and v.denominator == 1:
            return str(v.numerator)

    # Any standalone arithmetic expression line
    lines = [ln.strip() for ln in s.split("\n") if ln.strip()]
    for ln in reversed(lines[-6:]):
        if re.fullmatch(r'[0-9\(\)\+\-\*/\^\s%\.]+', ln):
            v = _safe_eval_expr(ln)
            if isinstance(v, Fraction) and v.denominator == 1:
                return str(v.numerator)

    # Linear equation in x
    lin = _parse_linear_eq(s)
    if lin is not None:
        return lin

    return "0"

def patch_solver(path="solver.py"):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()

    marker = "### AUREON_GENERAL_SOLVER_PATCH_V1 ###"
    if marker in src:
        return False

    patch = "\n\n" + marker + "\n" + r'''
# Appended deterministic general-solver fallback (no changes to existing override logic).
try:
    _AUREON__Solver = Solver  # type: ignore[name-defined]
except Exception:
    _AUREON__Solver = None

try:
    _AUREON__orig_solve = _AUREON__Solver.solve if _AUREON__Solver is not None else None
except Exception:
    _AUREON__orig_solve = None

# --- minimal general toolkit ---
''' + "\n" + "\n".join([
        _norm_text.__code__.co_consts[0] if False else ""  # placeholder; actual defs injected below
    ]) + "\n"

    # inject actual function source by embedding this module's functions
    import inspect
    patch += inspect.getsource(_norm_text) + "\n"
    patch += inspect.getsource(_safe_eval_expr) + "\n"
    patch += inspect.getsource(_parse_linear_eq) + "\n"
    patch += inspect.getsource(solve_general) + "\n"
    patch += r'''
def _AUREON__solve_wrapper(self, text):
    # preserve original behavior first
    if _AUREON__orig_solve is not None:
        try:
            out = _AUREON__orig_solve(self, text)
            out_s = str(out).strip() if out is not None else ""
            if out_s not in ("", "0"):
                return out_s
        except Exception:
            pass
    try:
        return solve_general(text)
    except Exception:
        return "0"

if _AUREON__Solver is not None:
    try:
        _AUREON__Solver.solve = _AUREON__solve_wrapper  # type: ignore[assignment]
    except Exception:
        pass
'''
    with open(path, "a", encoding="utf-8") as f:
        f.write(patch)
    return True

if __name__ == "__main__":
    changed = patch_solver("solver.py")
    print("PATCHED" if changed else "ALREADY_PATCHED")
