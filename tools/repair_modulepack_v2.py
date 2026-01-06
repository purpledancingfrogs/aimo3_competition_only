import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOLVER = ROOT / "solver.py"

MARK_B = "# === MODULEPACK_V2 BEGIN ==="
MARK_E = "# === MODULEPACK_V2 END ==="

RAW_BLOCK = r'''
# Deterministic bounded module pack v2 (self-contained). No prints.

import re as _mpv2_re
import math as _mpv2_math
import ast as _mpv2_ast
from fractions import Fraction as _mpv2_Fraction

def _mpv2_safe_eval_frac(expr: str):
    expr = expr.strip()
    if len(expr) > 256:
        return None
    expr = (expr.replace("−","-").replace("×","*").replace("·","*").replace("÷","/").replace("^","**"))
    if _mpv2_re.search(r"[A-Za-z_]", expr):
        return None
    try:
        tree = _mpv2_ast.parse(expr, mode="eval")
    except Exception:
        return None

    def ok_pow(a,b):
        if b.denominator != 1:
            return None
        n = int(b)
        if abs(n) > 12:
            return None
        if a.numerator == 0 and n < 0:
            return None
        try:
            return a ** n
        except Exception:
            return None

    def ev(n):
        if isinstance(n, _mpv2_ast.Expression):
            return ev(n.body)
        if isinstance(n, _mpv2_ast.Constant):
            if isinstance(n.value, (int, float)):
                return _mpv2_Fraction(n.value).limit_denominator()
            return None
        if isinstance(n, _mpv2_ast.UnaryOp) and isinstance(n.op, (_mpv2_ast.UAdd, _mpv2_ast.USub)):
            v = ev(n.operand)
            if v is None:
                return None
            return v if isinstance(n.op, _mpv2_ast.UAdd) else -v
        if isinstance(n, _mpv2_ast.BinOp):
            a = ev(n.left); b = ev(n.right)
            if a is None or b is None:
                return None
            if isinstance(n.op, _mpv2_ast.Add): return a + b
            if isinstance(n.op, _mpv2_ast.Sub): return a - b
            if isinstance(n.op, _mpv2_ast.Mult): return a * b
            if isinstance(n.op, _mpv2_ast.Div):
                if b == 0: return None
                return a / b
            if isinstance(n.op, _mpv2_ast.FloorDiv):
                if b == 0 or b.denominator != 1 or a.denominator != 1: return None
                return _mpv2_Fraction(int(a)//int(b), 1)
            if isinstance(n.op, _mpv2_ast.Mod):
                if b == 0 or b.denominator != 1 or a.denominator != 1: return None
                return _mpv2_Fraction(int(a)%int(b), 1)
            if isinstance(n.op, _mpv2_ast.Pow):
                return ok_pow(a,b)
            return None
        return None

    return ev(tree)

def _mpv2_try_linear(prompt: str):
    s = prompt.lower()
    s = s.replace("−","-").replace("×","*").replace("^","**")
    s = _mpv2_re.sub(r"[,\\n\\r\\t]", " ", s)
    s = _mpv2_re.sub(r"\\s+", " ", s).strip()
    m = _mpv2_re.search(r"(?<![a-z0-9_])([+-]?\\s*\\d*)\\s*\\*?\\s*x\\s*([+-]\\s*\\d+)?\\s*=\\s*([+-]?\\s*\\d+)(?![a-z0-9_])", s)
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
    if a == 0:
        return None
    num = c - b
    if num % a != 0:
        return None
    return str(num // a)

def _mpv2_try_quadratic_zero(prompt: str):
    s = prompt.lower().replace("−","-").replace("^","**")
    s = _mpv2_re.sub(r"[,\\n\\r\\t]", " ", s)
    s = _mpv2_re.sub(r"\\s+", " ", s).strip()
    s = s.replace("x^2","x**2")
    if "x**2" not in s:
        return None
    m = _mpv2_re.search(r"(?<![a-z0-9_])([+-]?\\s*\\d*)\\s*\\*?\\s*x\\*\\*2\\s*([+-]\\s*\\d*\\s*\\*?\\s*x)?\\s*([+-]\\s*\\d+)?\\s*=\\s*0(?![a-z0-9_])", s)
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
        bx_term = bx_term.replace("*","").replace("x","")
        if bx_term in ("+", ""): b = 1
        elif bx_term == "-": b = -1
        else:
            try: b = int(bx_term)
            except: return None
    c = 0
    if c_raw:
        try: c = int(c_raw)
        except: return None
    if a == 0:
        return None
    D = b*b - 4*a*c
    if D < 0:
        return None
    r = int(_mpv2_math.isqrt(D))
    if r*r != D:
        return None
    den = 2*a
    roots = []
    for num in (-b + r, -b - r):
        if den != 0 and num % den == 0:
            roots.append(num//den)
    roots = list(dict.fromkeys(roots))
    if len(roots) == 1:
        return str(roots[0])
    return None

def _mpv2_try_remainder_pow(prompt: str):
    s = prompt.lower().replace("−","-").replace("^","**")
    if "remainder" not in s and "mod" not in s:
        return None
    m = _mpv2_re.search(r"remainder\\s+when\\s+([+-]?\\d+)\\s*(?:\\^|\\*\\*\\s*)\\s*([+-]?\\d+)\\s+is\\s+divided\\s+by\\s+([+-]?\\d+)", s)
    if not m:
        m = _mpv2_re.search(r"([+-]?\\d+)\\s*(?:\\^|\\*\\*\\s*)\\s*([+-]?\\d+)\\s*mod\\s*([+-]?\\d+)", s)
    if not m:
        return None
    a = int(m.group(1)); b = int(m.group(2)); mod = int(m.group(3))
    if mod == 0 or b < 0 or abs(b) > 10**7:
        return None
    mod = abs(mod)
    return str(pow(a % mod, b, mod))

def _mpv2_try_gcd_lcm(prompt: str):
    s = prompt.lower().replace("−","-")
    nums = [int(x) for x in _mpv2_re.findall(r"(?<![a-z0-9_])[+-]?\\d+(?![a-z0-9_])", s)]
    if len(nums) < 2 or len(nums) > 6:
        return None
    if "gcd" in s or "greatest common divisor" in s:
        g = 0
        for v in nums[:2]:
            g = _mpv2_math.gcd(g, abs(v))
        return str(g)
    if "lcm" in s or "least common multiple" in s:
        a, b = abs(nums[0]), abs(nums[1])
        if a == 0 or b == 0:
            return None
        g = _mpv2_math.gcd(a,b)
        l = (a//g)*b
        if l > 10**18:
            return None
        return str(l)
    return None

def _mpv2_try_factorial(prompt: str):
    s = prompt.lower().replace("−","-")
    if "factorial" not in s and "!" not in s:
        return None
    m = _mpv2_re.search(r"(?<![a-z0-9_])(\\d{1,3})\\s*!", s)
    if not m:
        m = _mpv2_re.search(r"factorial\\s+of\\s+(\\d{1,3})", s)
    if not m:
        return None
    n = int(m.group(1))
    if n < 0 or n > 200:
        return None
    return str(_mpv2_math.factorial(n))

def _mpv2_try_nCk(prompt: str):
    s = prompt.lower()
    if "choose" not in s and "binomial" not in s and "combination" not in s and "c(" not in s:
        return None
    m = _mpv2_re.search(r"(?<![a-z0-9_])c\\s*\\(\\s*(\\d{1,4})\\s*,\\s*(\\d{1,4})\\s*\\)", s)
    if not m:
        m = _mpv2_re.search(r"(\\d{1,4})\\s+choose\\s+(\\d{1,4})", s)
    if not m:
        return None
    n = int(m.group(1)); k = int(m.group(2))
    if n < 0 or k < 0 or k > n or n > 5000:
        return None
    try:
        v = _mpv2_math.comb(n,k)
    except Exception:
        return None
    if v > 10**2000:
        return None
    return str(v)

def _mpv2_try_sum_first_n(prompt: str):
    s = prompt.lower().replace("−","-")
    m = _mpv2_re.search(r"sum\\s+of\\s+first\\s+(\\d{1,9})\\s+(?:positive\\s+)?integers", s)
    if not m:
        m = _mpv2_re.search(r"sum\\s+of\\s+the\\s+first\\s+(\\d{1,9})\\s+integers", s)
    if not m:
        return None
    n = int(m.group(1))
    if n < 0 or n > 10**9:
        return None
    return str(n*(n+1)//2)

def _mpv2_try_arith_expr(prompt: str):
    s = prompt.strip().replace("−","-").replace("×","*").replace("·","*").replace("÷","/").replace("^","**")
    cand = None
    for piece in _mpv2_re.split(r"[:=\\n\\r]", s):
        p = piece.strip()
        if _mpv2_re.search(r"\\d", p) and _mpv2_re.search(r"[\\+\\-\\*/%]", p) and len(p) <= 256:
            cand = p if (cand is None or len(p) > len(cand)) else cand
    if not cand:
        return None
    v = _mpv2_safe_eval_frac(cand)
    if v is None or v.denominator != 1:
        return None
    return str(int(v))

def _mpv2_try_solve(prompt: str):
    for fn in (
        _mpv2_try_linear,
        _mpv2_try_quadratic_zero,
        _mpv2_try_remainder_pow,
        _mpv2_try_gcd_lcm,
        _mpv2_try_factorial,
        _mpv2_try_nCk,
        _mpv2_try_sum_first_n,
        _mpv2_try_arith_expr,
    ):
        a = fn(prompt)
        if a is not None:
            return a
    return None

def _mpv2_install():
    try:
        cls = globals().get("Solver", None)
        if cls is not None and hasattr(cls, "solve"):
            _old = cls.solve
            def _new(self, prompt):
                a = _mpv2_try_solve(prompt)
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
                a = _mpv2_try_solve(prompt)
                if a is not None:
                    return a
                return _old2(prompt)
            globals()["solve"] = solve
    except Exception:
        pass

_mpv2_install()
'''

def repair():
    src = SOLVER.read_text(encoding="utf-8", errors="replace")
    pat = re.compile(re.escape(MARK_B) + r".*?" + re.escape(MARK_E), re.S)
    src = pat.sub("", src).rstrip() + "\n\n" + MARK_B + "\n" + RAW_BLOCK.strip("\n") + "\n" + MARK_E + "\n"
    SOLVER.write_text(src, encoding="utf-8")

if __name__ == "__main__":
    repair()
    print("REPAIRED")
