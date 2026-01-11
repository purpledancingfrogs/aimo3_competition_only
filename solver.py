from __future__ import annotations
import math
import re
import unicodedata
from typing import Any, List, Optional, Tuple

try:
    import sympy as sp
except ImportError:
    sp = None  # Kaggle may not have it; must not hard-fail

# ASIOS Core (κτΣ)
class ASIOS:
    def __init__(self):
        self.kappa = 1.0
        self.tau = 1.0
        self.sigma = 1.0
        self.trace = []

    def log_trace(self, step: str):
        self.trace.append(step)

    def check_invariants(self, prompt: str, answer: int) -> bool:
        # Verification must be non-blocking; if verify can't run, allow (do NOT force 0).
        self.log_trace("Σ-check: Verify")

        if answer is None:
            return False

        if sp is None:
            return True

        if "x" not in prompt or "=" not in prompt:
            return True

        try:
            parts = prompt.split("=")
            if len(parts) != 2:
                return True

            lhs_raw, rhs_raw = parts[0].strip(), parts[1].strip()
            x = sp.Symbol("x", integer=True)

            # 1) Try LaTeX parse (may fail on '*' style)
            try:
                lhs = sp.parse_latex(lhs_raw)
                rhs = sp.parse_latex(rhs_raw)
                expr = lhs - rhs
            except Exception:
                # 2) Fallback: sympify plain text (handles 2*x+3=11)
                def _to_sym(s: str):
                    s = s.replace("^", "**")
                    return sp.sympify(s, locals={"x": x})
                expr = _to_sym(lhs_raw) - _to_sym(rhs_raw)

            v = expr.subs(x, int(answer))

            # Avoid banned simplify(); use direct zero checks
            if v == 0:
                return True
            iz = getattr(v, "is_zero", None)
            if iz is True:
                return True
            if getattr(v, "is_number", False):
                try:
                    return int(v) == 0
                except Exception:
                    return False
            return False

        except Exception:
            return True

asios = ASIOS()

# Normalization
_ZW = dict.fromkeys(map(ord, ["\u200b", "\u200c", "\u200d", "\ufeff"]), None)

def _norm(s: Any) -> str:
    asios.log_trace("π-phase: Normalize")
    if s is None:
        return ""
    if not isinstance(s, str):
        try:
            s = str(s)
        except Exception:
            return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(_ZW)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return s.strip()

def _int_str(x: int) -> str:
    return str(int(x))

def _safe_int(s: str) -> Optional[int]:
    s = s.strip()
    if re.fullmatch(r"[+-]?\d+", s):
        try:
            return int(s)
        except Exception:
            return None
    return None

# Utilities
_RE_INT = r"[+-]?\d+"

def _egcd(a: int, b: int) -> Tuple[int, int, int]:
    asios.log_trace("φ-phase: EGCD")
    if b == 0:
        return (abs(a), 1 if a >= 0 else -1, 0)
    g, x1, y1 = _egcd(b, a % b)
    return g, y1, x1 - (a // b) * y1

def _crt_pair(a1: int, m1: int, a2: int, m2: int) -> Optional[Tuple[int, int]]:
    asios.log_trace("φ-phase: CRT Pair")
    if m1 == 0 or m2 == 0:
        return None
    m1, m2 = abs(m1), abs(m2)
    a1 %= m1
    a2 %= m2
    g, p, q = _egcd(m1, m2)
    if (a2 - a1) % g != 0:
        return None
    l = (m1 // g) * m2
    k = ((a2 - a1) // g) * p
    x = (a1 + (k % (m2 // g)) * m1) % l
    return x, l

def _solve_linear(a: int, b: int, c: int) -> Optional[int]:
    asios.log_trace("φ-phase: Linear Solve")
    if a == 0:
        return None
    num = c - b
    if num % a != 0:
        return None
    return num // a

def _det2(a: int, b: int, c: int, d: int) -> int:
    asios.log_trace("φ-phase: Det2")
    return a * d - b * c

def _cramer2(ax: int, by: int, e: int, cx: int, dy: int, f: int) -> Optional[Tuple[int, int]]:
    asios.log_trace("φ-phase: Cramer2")
    D = _det2(ax, by, cx, dy)
    if D == 0:
        return None
    Dx = _det2(e, by, f, dy)
    Dy = _det2(ax, e, cx, f)
    if Dx % D != 0 or Dy % D != 0:
        return None
    return Dx // D, Dy // D

# Solvers
def _try_simple_arithmetic(s: str) -> Optional[int]:
    asios.log_trace("e-phase: Simple Arithmetic")
    t = s.strip()
    m = re.search(r"(?is)\bsolve\s*:\s*(.+?)(?:\.\s*return\b|return\b|$)", t)
    if m:
        t = m.group(1).strip()
    m = re.search(r"(?is)\b(?:compute|evaluate)\s*:\s*(.+?)(?:\.\s*return\b|return\b|$)", t)
    if m:
        t = m.group(1).strip()
    if not re.fullmatch(r"[0-9\s\+\-\*\/\(\)]+", t):
        return None
    if "/" in t:
        return None
    try:
        val = eval(t, {"__builtins__": {}}, {})
    except Exception:
        return None
    return val if isinstance(val, int) else None

def _try_linear_equation(s: str) -> Optional[int]:
    asios.log_trace("e-phase: Linear Equation")
    t = s.replace(" ", "")
    t = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", t)
    m = re.search(rf"(?is)([+-]?\d+)\*?x([+-]\d+)?=([+-]?\d+)", t)
    if not m:
        return None
    a = int(m.group(1))
    b = int(m.group(2)) if m.group(2) else 0
    c = int(m.group(3))
    return _solve_linear(a, b, c)

def _try_system_sum_xy(s: str) -> Optional[int]:
    asios.log_trace("e-phase: System x+y")
    t = s
    if "x" not in t or "y" not in t or "=" not in t:
        return None
    wants_sum = bool(re.search(r"(?is)\breturn\s+x\s*\+\s*y\b", t)) or ("x+y" in t.replace(" ", ""))
    if not wants_sum:
        return None

    u = t.replace("\n", " ")
    u = re.sub(r"(\d)([xy])", r"\1*\2", u, flags=re.I)

    eqs = []
    pattern = re.compile(rf"(?is)([+-]?\d+)\s*\*\s*x\s*([+-]\s*\d+)\s*\*\s*y\s*=\s*([+-]?\d+)")
    for m in pattern.finditer(u):
        ax = int(m.group(1))
        by_ = int(m.group(2).replace(" ", ""))
        c = int(m.group(3))
        eqs.append((ax, by_, c))
        if len(eqs) >= 2:
            break

    if len(eqs) < 2:
        pattern2 = re.compile(rf"(?is)([+-]?\d+)?\s*\*?\s*x\s*([+-]\s*\d+)?\s*\*?\s*y\s*=\s*([+-]?\d+)")
        cand = []
        for m in pattern2.finditer(u):
            ax_s = m.group(1)
            by_s = m.group(2)
            c_s = m.group(3)
            if ax_s is None and by_s is None:
                continue
            ax = int(ax_s) if ax_s is not None else 1
            by_ = int(by_s.replace(" ", "")) if by_s is not None else 1
            c = int(c_s)
            cand.append((ax, by_, c))
        if len(cand) >= 2:
            eqs = cand

    if len(eqs) < 2:
        return None

    (a, b, e), (c, d, f) = eqs[0], eqs[1]
    sol = _cramer2(a, b, e, c, d, f)
    if sol is None:
        return None
    x, y = sol
    return x + y

def _try_crt(s: str) -> Optional[int]:
    asios.log_trace("e-phase: CRT")
    u = s
    if "mod" not in u.lower() and "≡" not in u:
        return None
    pairs: List[Tuple[int, int]] = []
    pat = re.compile(rf"(?is)x\s*(?:≡|=)\s*({_RE_INT})\s*(?:\(|\s)*mod\s*({_RE_INT})\s*\)?")
    for m in pat.finditer(u):
        a = int(m.group(1))
        mod = int(m.group(2))
        pairs.append((a, mod))
        if len(pairs) >= 3:
            break
    if len(pairs) < 2:
        pat2 = re.compile(rf"(?is)x\s+congruent\s+to\s+({_RE_INT})\s+mod\s+({_RE_INT})")
        for m in pat2.finditer(u):
            a = int(m.group(1))
            mod = int(m.group(2))
            pairs.append((a, mod))
            if len(pairs) >= 3:
                break
    if len(pairs) < 2:
        return None

    x0, m0 = pairs[0]
    x0 %= abs(m0)
    m0 = abs(m0)
    for a, m in pairs[1:]:
        res = _crt_pair(x0, m0, a, m)
        if res is None:
            return None
        x0, m0 = res
    return x0

def _try_gcd_lcm(s: str) -> Optional[int]:
    asios.log_trace("e-phase: GCD/LCM")
    u = s.lower()
    nums = [int(x) for x in re.findall(rf"{_RE_INT}", s)]
    if len(nums) < 2:
        return None
    if "gcd" in u or "greatest common divisor" in u:
        g = 0
        for n in nums:
            g = math.gcd(g, abs(n))
        return g
    if "lcm" in u or "least common multiple" in u:
        l = 1
        for n in nums:
            n = abs(n)
            if n == 0:
                return 0
            l = l // math.gcd(l, n) * n
            if l > 10**18:
                return None
        return l
    return None

def _try_factorial_digit_sum(s: str) -> Optional[int]:
    asios.log_trace("e-phase: Factorial Digit Sum")
    u = s.lower()
    if "digit" not in u or "!" not in s:
        return None
    m = re.search(rf"(?is)({_RE_INT})\s*!\s*", s)
    if not m:
        return None
    n = int(m.group(1))
    if n < 0 or n > 2000:
        return None
    try:
        val = math.factorial(n)
        return sum(int(ch) for ch in str(val))
    except Exception:
        return None

def _solve_one(prompt: str) -> str:
    asios.log_trace("π-phase: Prompt Perception")
    s = _norm(prompt)
    if not s:
        return "0"

    direct = _safe_int(s)
    if direct is not None and asios.check_invariants(s, direct):
        return _int_str(direct)

    for fn in [
        _try_simple_arithmetic,
        _try_linear_equation,
        _try_system_sum_xy,
        _try_crt,
        _try_gcd_lcm,
        _try_factorial_digit_sum,
    ]:
        try:
            ans = fn(s)
            if ans is not None and asios.check_invariants(s, ans):
                return _int_str(ans)
        except Exception:
            continue

    return "0"

def solve(prompt: Any) -> Any:
    if isinstance(prompt, (list, tuple)):
        return [_solve_one(p) for p in prompt]
    return _solve_one(prompt)