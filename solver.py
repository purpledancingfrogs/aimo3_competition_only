# solver.py — deterministic symbolic/regex solver (no LLM, no internet)
# Exposes solve(text) and CLI: python solver.py <stdin>
from __future__ import annotations

import re
import sys
import math
from fractions import Fraction

try:
    import sympy as sp  # type: ignore
except Exception:
    sp = None

_INT_RE = re.compile(r'[-+]?\d+')
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
    for _ in range(4):
        s2 = _LATEX_FRAC.sub(r'(\1)/(\2)', s)
        if s2 == s:
            break
        s = s2
    for _ in range(4):
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

def _safe_eval_expr(expr: str) -> Fraction | int:
    expr = expr.strip()
    if not expr:
        raise ValueError("empty expr")

    # Coerce all integer literals to Fraction to keep exact arithmetic under "/".
    def repl_int(m: re.Match) -> str:
        return f"F({m.group(0)},1)"
    expr_frac = re.sub(r'(?<![A-Za-z_])[-+]?\d+(?![A-Za-z_])', repl_int, expr)

    allowed = {
        "F": Fraction,
        "gcd": lambda a, b: Fraction(math.gcd(int(a), int(b)), 1),
        "lcm": lambda a, b: Fraction(abs(int(a) // math.gcd(int(a), int(b)) * int(b)) if int(a) and int(b) else 0, 1),
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
    if isinstance(val, int):
        return val
    return Fraction(float(val)).limit_denominator()

def _extract_arith_candidate(s: str) -> str | None:
    # Prefer expressions introduced by keywords.
    m = re.search(r'(?:what\s+is|compute|evaluate|simplify|calculate|find)\s*[:\-]?\s*([0-9\(\)\s\+\-\*\/\^\.,]+)\??',
                  s, re.IGNORECASE | re.DOTALL)
    if m:
        expr = m.group(1).replace(',', '').strip().rstrip('.').rstrip('?').rstrip('!').strip()
        if expr:
            return expr

    # Fallback: find a maximal operator-containing numeric expression anywhere.
    # Guardrails: no letters, short, must contain an operator and >= 2 numbers.
    best = None
    for mm in re.finditer(r'[-+*/^()\d\s\.,]{5,}', s):
        cand = mm.group(0)
        cand = cand.replace(',', '').strip().rstrip('.').rstrip('?').rstrip('!').strip()
        if not cand or len(cand) > 220:
            continue
        compact = re.sub(r'\s+', '', cand)
        if re.search(r'[A-Za-z_\\]', compact):
            continue
        if not re.search(r'[\+\-\*/\^]', compact):
            continue
        if len(re.findall(r'\d+', compact)) < 2:
            continue
        if best is None or len(compact) > len(best):
            best = compact
    return best

def _try_simple_arithmetic(s: str) -> int | None:
    expr = _extract_arith_candidate(s)
    if not expr:
        return None
    expr = _clean_text(expr)
    try:
        v = _safe_eval_expr(expr)
        return _safe_int(v)
    except Exception:
        return None

def _try_linear_equation(s: str) -> int | None:
    m = re.search(r'(?:solve|find|determine)\s*[:\-]?\s*([^\n]+?)\s*=\s*([^\n\.;]+)', s, re.IGNORECASE)
    if not m:
        return None
    left = _clean_text(m.group(1))
    right = _clean_text(m.group(2))
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

    expr = (left + " = " + right).replace(' ', '').replace('*', '')
    parts = expr.split('=')
    if len(parts) != 2:
        return None

    def parse_side(side: str):
        a = 0
        b = 0
        if side and side[0] not in '+-':
            side = '+' + side
        for term in re.finditer(r'([+-])([^+-]+)', side):
            sign = -1 if term.group(1) == '-' else 1
            t = term.group(2)
            if 'x' in t:
                coef = t.replace('x', '')
                coef = '1' if coef in ('', '+') else coef
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
    return int(math.floor(b / a))

def _try_remainder(s: str) -> int | None:
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

def solve(text: str) -> str:
    s = _clean_text(text or "")

    for fn in (_try_linear_equation, _try_simple_arithmetic, _try_remainder):
        try:
            ans = fn(s)
            if ans is not None:
                return str(int(ans))
        except Exception:
            continue

    return "0"

class Solver:
    def solve(self, text: str) -> str:
        return solve(text)

def _main():
    data = sys.stdin.read()
    sys.stdout.write(solve(data).strip())

if __name__ == "__main__":
    _main()