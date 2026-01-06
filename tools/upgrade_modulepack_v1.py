import re, ast, math
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOLVER = ROOT/"solver.py"

MARK_B = "# === MODULEPACK_V1 BEGIN ==="
MARK_E = "# === MODULEPACK_V1 END ==="

def _safe_eval_frac(expr: str):
    expr = expr.strip()
    if len(expr) > 256:
        return None
    expr = expr.replace("−","-").replace("×","*").replace("·","*").replace("÷","/").replace("^","**")
    # quick reject
    if re.search(r"[A-Za-z_]", expr):
        return None
    try:
        tree = ast.parse(expr, mode="eval")
    except Exception:
        return None

    def ok_pow(a,b):
        if b.denominator != 1: return None
        n = int(b)
        if abs(n) > 12: return None
        if a.numerator == 0 and n < 0: return None
        return a ** n

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant):
            if isinstance(n.value, (int, float)):
                return Fraction(n.value).limit_denominator()
            return None
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            v = ev(n.operand)
            if v is None: return None
            return v if isinstance(n.op, ast.UAdd) else -v
        if isinstance(n, ast.BinOp):
            a = ev(n.left); b = ev(n.right)
            if a is None or b is None: return None
            if isinstance(n.op, ast.Add): return a + b
            if isinstance(n.op, ast.Sub): return a - b
            if isinstance(n.op, ast.Mult): return a * b
            if isinstance(n.op, ast.Div):
                if b == 0: return None
                return a / b
            if isinstance(n.op, ast.FloorDiv):
                if b == 0 or b.denominator != 1 or a.denominator != 1: return None
                return Fraction(int(a)//int(b), 1)
            if isinstance(n.op, ast.Mod):
                if b == 0 or b.denominator != 1 or a.denominator != 1: return None
                return Fraction(int(a)%int(b), 1)
            if isinstance(n.op, ast.Pow):
                return ok_pow(a,b)
            return None
        return None

    return ev(tree)

def _try_linear(prompt: str):
    s = prompt.lower()
    s = s.replace("−","-").replace("×","*").replace("^","**")
    s = re.sub(r"[,\n\r\t]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    # accept forms: ax+b=c ; ax-b=c ; x+b=c ; -x+b=c ; 2*x+3=11 ; 2x+3=11
    m = re.search(r"(?<![a-z0-9_])([+-]?\s*\d*)\s*\*?\s*x\s*([+-]\s*\d+)?\s*=\s*([+-]?\s*\d+)(?![a-z0-9_])", s)
    if not m:
        return None
    a_raw = m.group(1).replace(" ","")
    b_raw = (m.group(2) or "").replace(" ","")
    c_raw = m.group(3).replace(" ","")
    if a_raw in ("", "+"): a = 1
    elif a_raw == "-": a = -1
    else:
        try: a = int(a_raw)
        except: return None
    b = 0
    if b_raw:
        try: b = int(b_raw)
        except: return None
    try: c = int(c_raw)
    except: return None
    if a == 0: return None
    num = c - b
    if num % a != 0: return None
    return str(num // a)

def _try_quadratic(prompt: str):
    s = prompt.lower().replace("−","-").replace("^","**")
    s = re.sub(r"[,\n\r\t]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    # Normalize x^2 / x**2
    s = s.replace("x^2","x**2")
    if "x**2" not in s:
        return None

    # capture "ax**2 + bx + c = 0" (a,b,c ints; allow missing b/c; allow a=1/-1)
    m = re.search(r"(?<![a-z0-9_])([+-]?\s*\d*)\s*\*?\s*x\*\*2\s*([+-]\s*\d*\s*\*?\s*x)?\s*([+-]\s*\d+)?\s*=\s*0(?![a-z0-9_])", s)
    if not m:
        return None

    a_raw = m.group(1).replace(" ","")
    bx_term = (m.group(2) or "").replace(" ","")
    c_raw = (m.group(3) or "").replace(" ","")

    if a_raw in ("", "+"): a = 1
    elif a_raw == "-": a = -1
    else:
        try: a = int(a_raw)
        except: return None

    b = 0
    if bx_term:
        # bx_term like "+3*x" or "-x" or "+2x"
        bx_term = bx_term.replace("*","")
        bx_term = bx_term.replace("x","")
        if bx_term in ("+", ""): b = 1
        elif bx_term == "-": b = -1
        else:
            try: b = int(bx_term)
            except: return None

    c = 0
    if c_raw:
        try: c = int(c_raw)
        except: return None

    if a == 0: return None
    D = b*b - 4*a*c
    if D < 0: return None
    r = int(math.isqrt(D))
    if r*r != D: return None
    # integer roots
    den = 2*a
    roots = []
    for num in (-b + r, -b - r):
        if den != 0 and num % den == 0:
            roots.append(num//den)
    roots = list(dict.fromkeys(roots))
    if len(roots) == 1:
        return str(roots[0])
    # if prompt asks "sum of roots" etc we skip (unknown target)
    return None

def _try_arith(prompt: str):
    # extract a plausible expression tail
    s = prompt.strip()
    s = s.replace("−","-").replace("×","*").replace("·","*").replace("÷","/").replace("^","**")
    # pick the longest operator-rich substring
    cand = None
    for piece in re.split(r"[:=\n\r]", s):
        p = piece.strip()
        if re.search(r"\d", p) and re.search(r"[\+\-\*/%]", p) and len(p) <= 256:
            cand = p if (cand is None or len(p) > len(cand)) else cand
    if not cand:
        return None
    v = _safe_eval_frac(cand)
    if v is None: return None
    if v.denominator != 1: return None
    return str(int(v))

def try_solve(prompt: str):
    for fn in (_try_linear, _try_quadratic, _try_arith):
        ans = fn(prompt)
        if ans is not None:
            return ans
    return None

def patch_solver():
    src = SOLVER.read_text(encoding="utf-8", errors="replace")
    if MARK_B in src and MARK_E in src:
        return False

    block = f"""
{MARK_B}
# Deterministic bounded module pack. No prints. Returns integer-string or None.

def _mpv1_try_solve(_prompt: str):
    try:
        return try_solve(_prompt)
    except Exception:
        return None

def _mpv1_install():
    # Prefer patching Solver.solve; fallback to module-level solve(prompt)
    try:
        cls = globals().get("Solver", None)
        if cls is not None and hasattr(cls, "solve"):
            _old = cls.solve
            def _new(self, prompt):
                a = _mpv1_try_solve(prompt)
                if a is not None:
                    return a
                return _old(self, prompt)
            cls.solve = _new
            return
    except Exception:
        pass
    try:
        if "solve" in globals() and callable(globals()["solve"]):
            _old2 = globals()["solve"]
            def solve(prompt):
                a = _mpv1_try_solve(prompt)
                if a is not None:
                    return a
                return _old2(prompt)
            globals()["solve"] = solve
    except Exception:
        pass

_mpv1_install()
{MARK_E}
"""
    SOLVER.write_text(src.rstrip()+"\n"+block.lstrip(), encoding="utf-8")
    return True

if __name__ == "__main__":
    changed = patch_solver()
    print("PATCHED" if changed else "ALREADY_PATCHED")
