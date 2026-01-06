# tools/upgrade_modulepack_v3.py
# Deterministic, bounded, self-contained patcher: inject/replace APEX_MODULEPACK_V3 block in solver.py

from __future__ import annotations
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOLVER = ROOT / "solver.py"

BEGIN = "# === APEX_MODULEPACK_V3_BEGIN ==="
END   = "# === APEX_MODULEPACK_V3_END ==="

BLOCK = r'''
# === APEX_MODULEPACK_V3_BEGIN ===
# Deterministic general hard-solver fallback (bounded). No file/network IO. No randomness.

import re as _re
import math as _math
from typing import Optional as _Optional

try:
    import sympy as _sp
    from sympy.parsing.sympy_parser import (
        parse_expr as _parse_expr,
        standard_transformations as _std_tr,
        implicit_multiplication_application as _impl_mul,
        convert_xor as _cxor,
    )
    _SYM_OK = True
except Exception:
    _SYM_OK = False
    _sp = None

_mpv3_tr = _std_tr + (_impl_mul, _cxor) if _SYM_OK else None

# Hard caps (do not exceed)
_MPV3_MAX_CHARS = 9000
_MPV3_MAX_TOKENS = 2500
_MPV3_SOLVE_TIMEOUT_MS = 1200  # soft guard via bounded operations (no true timeouts)
_MPV3_MAX_SOLNS = 8

# Normalization helpers
_mpv3_ws = _re.compile(r"[ \t]+")
_mpv3_unicode_minus = _re.compile(r"[\u2212\u2013\u2014]")  # − – —
_mpv3_frac = _re.compile(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}")
_mpv3_sqrt = _re.compile(r"\\sqrt\s*\{([^{}]+)\}")
_mpv3_texcmd = _re.compile(r"\\(left|right|cdot|times|,|;|!|quad|qquad)\b")
_mpv3_dollars = _re.compile(r"\$")
_mpv3_braces = _re.compile(r"[{}]")
_mpv3_pi = _re.compile(r"\\pi\b")
_mpv3_pow = _re.compile(r"\^")
_mpv3_mult = _re.compile(r"(?<=\d)\s*(?=[a-zA-Z(])")  # 2x -> 2*x
_mpv3_eqsplit = _re.compile(r"(?<![<>=])=(?![<>=])")

def _mpv3_norm(s: str) -> str:
    s = s.strip()
    if not s:
        return s
    if len(s) > _MPV3_MAX_CHARS:
        s = s[:_MPV3_MAX_CHARS]
    s = _mpv3_dollars.sub(" ", s)
    s = _mpv3_unicode_minus.sub("-", s)
    # TeX -> plain
    for _ in range(6):
        s2 = _mpv3_frac.sub(r"(\1)/(\2)", s)
        s2 = _mpv3_sqrt.sub(r"sqrt(\1)", s2)
        if s2 == s:
            break
        s = s2
    s = _mpv3_pi.sub("pi", s)
    s = _mpv3_texcmd.sub(" ", s)
    s = _mpv3_braces.sub(" ", s)
    s = _mpv3_pow.sub("**", s)
    s = s.replace("×", "*").replace("·", "*")
    s = s.replace("÷", "/")
    s = s.replace("∕", "/")
    s = s.replace("≤", "<=").replace("≥", ">=")
    s = s.replace("≠", "!=")
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = _mpv3_ws.sub(" ", s)
    return s.strip()

def _mpv3_int(x) -> _Optional[int]:
    try:
        if x is None:
            return None
        if isinstance(x, bool):
            return int(x)
        if isinstance(x, int):
            return x
        if _SYM_OK and isinstance(x, _sp.Integer):
            return int(x)
        if _SYM_OK and hasattr(x, "is_integer") and x.is_integer is True:
            return int(x)
        # rational -> int if exact
        if _SYM_OK and isinstance(x, _sp.Rational):
            if x.q == 1:
                return int(x.p)
            return None
        # float -> int if close (tight)
        if isinstance(x, float):
            if _math.isfinite(x) and abs(x - round(x)) < 1e-9:
                return int(round(x))
            return None
        # string numeric
        if isinstance(x, str):
            t = x.strip()
            if _re.fullmatch(r"-?\d+", t):
                return int(t)
        return None
    except Exception:
        return None

def _mpv3_parse_expr(expr: str):
    if not _SYM_OK:
        return None
    expr = expr.strip()
    if not expr:
        return None
    # prevent pathological length
    if len(expr) > 2000:
        return None
    # cheap token cap
    if len(_re.findall(r"[A-Za-z_]\w*|\d+|\S", expr)) > _MPV3_MAX_TOKENS:
        return None
    local = {
        "pi": _sp.pi,
        "sqrt": _sp.sqrt,
        "Abs": _sp.Abs,
        "abs": _sp.Abs,
        "floor": _sp.floor,
        "ceiling": _sp.ceiling,
        "ceil": _sp.ceiling,
        "log": _sp.log,
        "ln": _sp.log,
        "exp": _sp.exp,
        "sin": _sp.sin,
        "cos": _sp.cos,
        "tan": _sp.tan,
        "asin": _sp.asin,
        "acos": _sp.acos,
        "atan": _sp.atan,
        "gcd": _sp.gcd,
        "lcm": _sp.ilcm,
        "binomial": _sp.binomial,
        "factorial": _sp.factorial,
    }
    try:
        return _parse_expr(expr, transformations=_mpv3_tr, local_dict=local, evaluate=True)
    except Exception:
        return None

def _mpv3_try_mod(s: str) -> _Optional[int]:
    # e.g. "Calculate 15 mod 4" / "15 modulo 4" / "15 (mod 4)"
    m = _re.search(r"(-?\d+)\s*(?:mod(?:ulo)?|\(mod)\s*(-?\d+)\)?", s, flags=_re.I)
    if not m:
        return None
    a = int(m.group(1)); n = int(m.group(2))
    if n == 0:
        return None
    return a % n

def _mpv3_try_direct_eval(s: str) -> _Optional[int]:
    if not _SYM_OK:
        return None
    # find likely expression after cues
    cues = ["compute", "calculate", "evaluate", "find", "determine", "value of", "what is", "simplify"]
    low = s.lower()
    start = 0
    for c in cues:
        j = low.find(c)
        if j != -1:
            start = max(start, j + len(c))
    tail = s[start:].strip()
    # strip trailing question
    tail = tail.rstrip(" ?.")
    if not tail:
        return None
    e = _mpv3_parse_expr(tail)
    if e is None:
        return None
    try:
        e2 = _sp.simplify(e)
        return _mpv3_int(e2)
    except Exception:
        return None

def _mpv3_try_equation(s: str) -> _Optional[int]:
    if not _SYM_OK:
        return None
    # detect single-variable equation, solve for common vars
    # extract best candidate equation substring containing '='
    if "=" not in s:
        return None
    parts = _mpv3_eqsplit.split(s)
    if len(parts) < 2:
        return None
    # take first '=' split
    lhs = parts[0].strip()
    rhs = parts[1].strip()
    # trim excessive context around lhs/rhs
    lhs = lhs.split("\n")[-1].strip()
    rhs = rhs.split("\n")[0].strip()
    lhs = lhs.rstrip(" ,;:.")
    rhs = rhs.rstrip(" ,;:.")
    if not lhs or not rhs:
        return None
    L = _mpv3_parse_expr(lhs)
    R = _mpv3_parse_expr(rhs)
    if L is None or R is None:
        return None

    # choose variable
    cand_vars = []
    for v in ["x","y","z","n","k","m","t"]:
        if _re.search(rf"\b{v}\b", s):
            cand_vars.append(v)
    if not cand_vars:
        # fallback: any single-letter symbol
        cand_vars = list(dict.fromkeys(_re.findall(r"\b([a-zA-Z])\b", s)))
    if not cand_vars:
        return None

    for v in cand_vars[:2]:
        X = _sp.Symbol(v, integer=True)
        try:
            eq = _sp.Eq(L, R)
            sol = _sp.solve(eq, X, dict=False)
            if isinstance(sol, (list, tuple)):
                sol = sol[:_MPV3_MAX_SOLNS]
                ints = [ _mpv3_int(si) for si in sol ]
                ints = [i for i in ints if i is not None]
                if len(ints) == 1:
                    # plugback verify
                    try:
                        ok = _sp.simplify(eq.subs({X: ints[0]})) == True
                        if ok:
                            return ints[0]
                    except Exception:
                        return ints[0]
        except Exception:
            continue
    return None

def _mpv3_try_system(s: str) -> _Optional[int]:
    if not _SYM_OK:
        return None
    # very small linear system: lines containing '=' and variables, goal typically "x+y" / "x"
    eq_lines = [ln.strip() for ln in s.split("\n") if "=" in ln]
    if len(eq_lines) < 2 or len(eq_lines) > 5:
        return None
    eqs = []
    syms = {}
    for ln in eq_lines[:5]:
        parts = _mpv3_eqsplit.split(ln)
        if len(parts) < 2:
            continue
        lhs = _mpv3_parse_expr(parts[0].strip())
        rhs = _mpv3_parse_expr(parts[1].strip())
        if lhs is None or rhs is None:
            continue
        eqs.append(_sp.Eq(lhs, rhs))
        for sym in (lhs.free_symbols | rhs.free_symbols):
            if sym.name not in syms and len(sym.name) <= 2:
                syms[sym.name] = _sp.Symbol(sym.name, integer=True)
    if len(eqs) < 2:
        return None

    # decide target: "x+y", else "x", else any
    target_expr = None
    low = s.lower()
    if "x+y" in low or "x + y" in low:
        X = syms.get("x", _sp.Symbol("x", integer=True))
        Y = syms.get("y", _sp.Symbol("y", integer=True))
        target_expr = X + Y
    elif _re.search(r"\bfind\b.*\bx\b", low) or _re.search(r"\bvalue of x\b", low):
        target_expr = syms.get("x", _sp.Symbol("x", integer=True))
    if target_expr is None:
        # first symbol
        k = next(iter(syms.keys()), None)
        if k is None:
            return None
        target_expr = syms[k]

    try:
        sol = _sp.solve(eqs, list(syms.values()), dict=True)
        if isinstance(sol, list) and sol:
            sol = sol[:_MPV3_MAX_SOLNS]
            vals = []
            for d in sol:
                try:
                    v = _sp.simplify(target_expr.subs(d))
                    iv = _mpv3_int(v)
                    if iv is not None:
                        vals.append(iv)
                except Exception:
                    pass
            vals = list(dict.fromkeys(vals))
            if len(vals) == 1:
                return vals[0]
    except Exception:
        return None
    return None

def _mpv3_try_combinatorics(s: str) -> _Optional[int]:
    if not _SYM_OK:
        return None
    # n choose k cues
    m = _re.search(r"\b(?:choose|binomial)\b", s, flags=_re.I)
    if m:
        # attempt to parse "C(n,k)" or "n choose k"
        m2 = _re.search(r"(\d+)\s*(?:choose|C)\s*(\d+)", s, flags=_re.I)
        if not m2:
            m2 = _re.search(r"C\(\s*(\d+)\s*,\s*(\d+)\s*\)", s, flags=_re.I)
        if m2:
            n = int(m2.group(1)); k = int(m2.group(2))
            if 0 <= k <= n <= 5000:
                return _mpv3_int(_sp.binomial(n, k))
    # factorial
    m3 = _re.search(r"\b(\d+)\s*!\b", s)
    if m3:
        n = int(m3.group(1))
        if 0 <= n <= 2000:
            return _mpv3_int(_sp.factorial(n))
    return None

def _mpv3_solve(prompt: str) -> _Optional[int]:
    try:
        if not isinstance(prompt, str):
            prompt = str(prompt)
        s = _mpv3_norm(prompt)
        if not s:
            return 0
        # quick mod
        a = _mpv3_try_mod(s)
        if a is not None:
            return int(a)
        # systems
        a = _mpv3_try_system(s)
        if a is not None:
            return int(a)
        # equation
        a = _mpv3_try_equation(s)
        if a is not None:
            return int(a)
        # combinatorics
        a = _mpv3_try_combinatorics(s)
        if a is not None:
            return int(a)
        # direct eval
        a = _mpv3_try_direct_eval(s)
        if a is not None:
            return int(a)
        return None
    except Exception:
        return None

def _apex_wrap_solver_v3():
    # Wrap existing Solver.solve while preserving overrides and earlier modulepacks.
    g = globals()
    if "Solver" not in g:
        return
    S = g["Solver"]
    if getattr(S, "_apex_v3_wrapped", False):
        return
    orig = getattr(S, "solve", None)
    if orig is None:
        return

    def solve(self, text):
        try:
            ans = _mpv3_solve(text)
            if ans is not None:
                return str(int(ans))
        except Exception:
            pass
        try:
            return orig(self, text)
        except Exception:
            return "0"

    S.solve = solve
    S._apex_v3_wrapped = True

_apex_wrap_solver_v3()

# === APEX_MODULEPACK_V3_END ===
'''

def main():
    raw = SOLVER.read_text(encoding="utf-8")
    if BEGIN in raw and END in raw:
        pat = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.DOTALL)
        raw2 = pat.sub(BLOCK.strip("\n"), raw)
    else:
        if not raw.endswith("\n"):
            raw += "\n"
        raw2 = raw + "\n" + BLOCK.strip("\n") + "\n"
    SOLVER.write_text(raw2, encoding="utf-8")
    print("PATCHED_V3")

if __name__ == "__main__":
    main()
