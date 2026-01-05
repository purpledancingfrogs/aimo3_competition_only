# solver.py — deterministic symbolic/regex solver (no LLM, no internet)
# Exposes solve(text) and CLI: python solver.py <stdin>
from __future__ import annotations

import re
import sys
import math
from fractions import Fraction

# Optional sympy (available on many Kaggle images; safe to import if present)
try:
    import sympy as sp  # type: ignore
except Exception:
    sp = None

_INT_RE = re.compile(r'[-+]?\d+')
_WS = re.compile(r'\s+')
_LATEX_FRAC = re.compile(r'\\frac\{([^{}]+)\}\{([^{}]+)\}')
_LATEX_BINOM = re.compile(r'\\binom\{([^{}]+)\}\{([^{}]+)\}')
_LATEX_TIMES = re.compile(r'\\cdot|\\times')
_LATEX_GE = re.compile(r'\\geq|\\ge')
_LATEX_LE = re.compile(r'\\leq|\\le')
_LATEX_NE = re.compile(r'\\neq')
_LATEX_LFLOOR = re.compile(r'\\left\\lfloor|\\lfloor')
_LATEX_RFLOOR = re.compile(r'\\right\\rfloor|\\rfloor')
_LATEX_LCEIL = re.compile(r'\\left\\lceil|\\lceil')
_LATEX_RCEIL = re.compile(r'\\right\\rceil|\\rceil')

def _clean_text(s: str) -> str:
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    s = _LATEX_TIMES.sub('*', s)
    s = _LATEX_GE.sub('>=', s)
    s = _LATEX_LE.sub('<=', s)
    s = _LATEX_NE.sub('!=', s)
    s = _LATEX_LFLOOR.sub('floor(', s)
    s = _LATEX_RFLOOR.sub(')', s)
    s = _LATEX_LCEIL.sub('ceil(', s)
    s = _LATEX_RCEIL.sub(')', s)
    # \frac{a}{b} -> (a)/(b)
    for _ in range(3):
        s2 = _LATEX_FRAC.sub(r'(\1)/(\2)', s)
        if s2 == s:
            break
        s = s2
    # \binom{n}{k} -> C(n,k)
    for _ in range(3):
        s2 = _LATEX_BINOM.sub(r'C(\1,\2)', s)
        if s2 == s:
            break
        s = s2
    s = s.replace('^', '**')
    s = s.replace('–', '-').replace('−', '-').replace('×', '*').replace('·', '*')
    return s

def _safe_int(x) -> int:
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, int):
        return x
    if isinstance(x, Fraction):
        if x.denominator == 1:
            return int(x.numerator)
        # For contest answers, prefer exact integer only; otherwise floor
        return int(math.floor(x))
    try:
        if sp is not None and isinstance(x, sp.Basic):
            if x.is_integer is True:
                return int(x)
            if x.is_Rational:
                return int(sp.floor(x))
    except Exception:
        pass
    try:
        xf = float(x)
        if abs(xf - round(xf)) < 1e-12:
            return int(round(xf))
        return int(math.floor(xf))
    except Exception:
        return 0

def _C(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)

def _gcd(a: int, b: int) -> int:
    return math.gcd(a, b)

def _lcm(a: int, b: int) -> int:
    return abs(a // math.gcd(a, b) * b) if a and b else 0

def _safe_eval_expr(expr: str) -> Fraction | int:
    """
    Deterministic arithmetic evaluator for expressions consisting of:
    integers, + - * / ** parentheses, and functions: gcd, lcm, C, floor, ceil.
    Uses Python eval with locked globals and Fraction for exact division.
    """
    expr = expr.strip()
    if not expr:
        raise ValueError("empty expr")

    # Replace integer divisions to exact Fractions by wrapping "/" operands via Fraction through eval namespace.
    # We keep "/" as true division; Python will use int->float unless we coerce.
    # Easiest: replace all integers with Fraction(int,1) tokens for eval.
    def repl_int(m):
        return f"F({m.group(0)},1)"
    expr_frac = re.sub(r'(?<![A-Za-z_])[-+]?\d+(?![A-Za-z_])', repl_int, expr)

    allowed = {
        "F": Fraction,
        "gcd": lambda a, b: Fraction(_gcd(int(a), int(b)), 1),
        "lcm": lambda a, b: Fraction(_lcm(int(a), int(b)), 1),
        "C": lambda n, k: Fraction(_C(int(n), int(k)), 1),
        "floor": lambda x: Fraction(math.floor(float(x)), 1),
        "ceil": lambda x: Fraction(math.ceil(float(x)), 1),
        "abs": lambda x: Fraction(abs(float(x)), 1),
    }
    val = eval(expr_frac, {"__builtins__": {}}, allowed)  # noqa: S307
    if isinstance(val, Fraction):
        if val.denominator == 1:
            return int(val.numerator)
        return val
    if isinstance(val, (int,)):
        return val
    # fall back
    return Fraction(float(val)).limit_denominator()

def _try_simple_arithmetic(s: str) -> int | None:
    # Patterns like "What is 1-1?" or "Compute 2*(3+4)."
    m = re.search(r'(?:what is|compute|evaluate|find)\s*[:\-]?\s*([0-9\(\)\s\+\-\*\/\^\.,]+)\??', s, re.IGNORECASE)
    if not m:
        return None
    expr = m.group(1)
    expr = expr.replace(',', '').strip().rstrip('.')
    expr = _clean_text(expr)
    try:
        v = _safe_eval_expr(expr)
        return _safe_int(v)
    except Exception:
        return None

def _try_linear_equation(s: str) -> int | None:
    # Matches: solve 2*x + 3 = 11
    m = re.search(r'(?:solve|find|determine)\s*[:\-]?\s*([^\n]+?)\s*=\s*([^\n\.;]+)', s, re.IGNORECASE)
    if not m:
        return None
    left = _clean_text(m.group(1))
    right = _clean_text(m.group(2))
    # If clearly a single-variable x equation, solve via sympy if available; else manual for ax+b=c
    if 'x' not in left and 'x' not in right:
        return None

    if sp is not None:
        x = sp.Symbol('x')
        try:
            eq = sp.Eq(sp.sympify(left, locals={"x": x}), sp.sympify(right, locals={"x": x}))
            sol = sp.solve(eq, x)
            if sol:
                return _safe_int(sol[0])
        except Exception:
            pass

    # Manual fallback: ax + b = c with integers
    # Normalize like: 2*x+3=11, 3*x-5=16, -x+7=2
    expr = (left + " = " + right).replace(' ', '')
    expr = expr.replace('*', '')
    # Bring to ax+b=c where a,b,c ints
    # Parse left as ax + b
    def parse_side(side: str):
        a = 0
        b = 0
        # Ensure leading sign
        if side and side[0] not in '+-':
            side = '+' + side
        # Tokenize terms: ±... where term can be x, nx, or integer
        for term in re.finditer(r'([+-])([^+-]+)', side):
            sign = -1 if term.group(1) == '-' else 1
            t = term.group(2)
            if 'x' in t:
                coef = t.replace('x', '')
                coef = coef if coef not in ('', '+') else '1'
                coef = '-1' if coef == '-' else coef
                try:
                    a += sign * int(coef)
                except Exception:
                    return None
            else:
                try:
                    b += sign * int(t)
                except Exception:
                    return None
        return a, b

    parts = expr.split('=')
    if len(parts) != 2:
        return None
    L = parse_side(parts[0])
    R = parse_side(parts[1])
    if L is None or R is None:
        return None
    aL, bL = L
    aR, bR = R
    a = aL - aR
    b = bR - bL
    if a == 0:
        return None
    if b % a == 0:
        return b // a
    # If non-integer, return floor
    return int(math.floor(b / a))

def _try_remainder(s: str) -> int | None:
    # "remainder when A is divided by B"
    m = re.search(r'remainder\s+when\s+(.+?)\s+is\s+divided\s+by\s+(.+?)[\.\?]', s, re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    a_txt = _clean_text(m.group(1))
    b_txt = _clean_text(m.group(2))
    try:
        a = _safe_int(_safe_eval_expr(a_txt))
        b = _safe_int(_safe_eval_expr(b_txt))
        if b == 0:
            return None
        return a % b
    except Exception:
        return None

def _extract_last_int(s: str) -> int | None:
    # If prompt includes "Return final integer only." and there is an explicit numeric result embedded
    ints = _INT_RE.findall(s.replace(',', ''))
    if not ints:
        return None
    try:
        return int(ints[-1])
    except Exception:
        return None

def solve(text: str) -> str:
    s0 = text or ""
    s = _clean_text(s0)

    for fn in (_try_linear_equation, _try_simple_arithmetic, _try_remainder):
        try:
            ans = fn(s)
            if ans is not None:
                return str(int(ans))
        except Exception:
            continue

    # No safe solve found
    return "0"

class Solver:
    def solve(self, text: str) -> str:
        return solve(text)

def _main():
    data = sys.stdin.read()
    out = solve(data)
    sys.stdout.write(str(out).strip())

if __name__ == "__main__":
    _main()