# solver.py — deterministic symbolic/regex solver (no LLM, no internet)
# Exposes solve(text) and CLI: python solver.py <stdin>
from __future__ import annotations

from modules.number_theory import try_modular
from modules.fractal_geometry import try_fractal_dimension, dimension_value
from modules.fractal_geometry import try_fractal_counts
import re
import sys
import math
import ast
from fractions import Fraction

try:
    import sympy as sp  # type: ignore
except Exception:
    sp = None

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

def _safe_int(v) -> int:
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, int):
        return v
    if isinstance(v, Fraction):
        if v.denominator == 1:
            return int(v.numerator)
        return int(math.floor(v.numerator / v.denominator))
    try:
        if sp is not None and isinstance(v, sp.Basic):
            if v.is_integer is True:
                return int(v)
            if v.is_Rational:
                return int(sp.floor(v))
    except Exception:
        pass
    try:
        fv = float(v)
        if abs(fv - round(fv)) < 1e-12:
            return int(round(fv))
        return int(math.floor(fv))
    except Exception:
        return 0

def _C(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)

def _eval_ast(expr: str) -> Fraction:
    node = ast.parse(expr, mode="eval")

    def ev(n) -> Fraction:
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant):
            if isinstance(n.value, (int, bool)):
                return Fraction(int(n.value), 1)
            raise ValueError("bad const")
        if isinstance(n, ast.UnaryOp):
            v = ev(n.operand)
            if isinstance(n.op, ast.UAdd):
                return v
            if isinstance(n.op, ast.USub):
                return -v
            raise ValueError("bad unary")
        if isinstance(n, ast.BinOp):
            a = ev(n.left)
            b = ev(n.right)
            if isinstance(n.op, ast.Add):
                return a + b
            if isinstance(n.op, ast.Sub):
                return a - b
            if isinstance(n.op, ast.Mult):
                return a * b
            if isinstance(n.op, ast.Div):
                if b == 0:
                    raise ZeroDivisionError
                return a / b
            if isinstance(n.op, ast.Pow):
                if b.denominator != 1:
                    raise ValueError("non-integer exponent")
                e = int(b.numerator)
                if abs(e) > 4096:
                    raise ValueError("exp too large")
                if e >= 0:
                    return a ** e
                if a == 0:
                    raise ZeroDivisionError
                return Fraction(1, 1) / (a ** (-e))
            if isinstance(n.op, ast.Mod):
                if b == 0:
                    raise ZeroDivisionError
                if a.denominator != 1 or b.denominator != 1:
                    raise ValueError("mod needs ints")
                return Fraction(int(a.numerator) % int(b.numerator), 1)
            raise ValueError("bad binop")
        if isinstance(n, ast.Call):
            if not isinstance(n.func, ast.Name):
                raise ValueError("bad call")
            fname = n.func.id
            args = [ev(a) for a in n.args]
            if fname == "gcd":
                if len(args) != 2:
                    raise ValueError("gcd arity")
                return Fraction(math.gcd(int(args[0]), int(args[1])), 1)
            if fname == "lcm":
                if len(args) != 2:
                    raise ValueError("lcm arity")
                a0 = int(args[0]); b0 = int(args[1])
                if a0 == 0 or b0 == 0:
                    return Fraction(0, 1)
                return Fraction(abs(a0 // math.gcd(a0, b0) * b0), 1)
            if fname == "C":
                if len(args) != 2:
                    raise ValueError("C arity")
                return Fraction(_C(int(args[0]), int(args[1])), 1)
            if fname == "floor":
                if len(args) != 1:
                    raise ValueError("floor arity")
                x = args[0]
                return Fraction(math.floor(x.numerator / x.denominator), 1)
            if fname == "ceil":
                if len(args) != 1:
                    raise ValueError("ceil arity")
                x = args[0]
                return Fraction(math.ceil(x.numerator / x.denominator), 1)
            if fname == "abs":
                if len(args) != 1:
                    raise ValueError("abs arity")
                return abs(args[0])
            raise ValueError("bad func")
        raise ValueError("bad node")

    return ev(node)

def _safe_eval_expr(expr: str) -> Fraction | int:
    expr = expr.strip()
    if not expr:
        raise ValueError("empty")
    expr = expr.replace(",", "")
    v = _eval_ast(expr)
    if v.denominator == 1:
        return int(v.numerator)
    return v

def _extract_arith_candidate(s: str) -> str | None:
    # capture until end-of-sentence punctuation or newline
    m = re.search(r'(?:what\s+is|compute|evaluate|simplify|calculate)\s*[:\-]?\s*(.+?)(?:[?\.\n]|$)',
                  s, re.IGNORECASE | re.DOTALL)
    if m:
        expr = m.group(1).strip()
        expr = expr.rstrip('?').rstrip('.').rstrip('!').strip()
        if expr:
            return expr

    # fallback: longest operator-containing numeric expression
    best = None
    for mm in re.finditer(r'[-+*/^()\d\s\.,]{5,}', s):
        cand = mm.group(0).replace(",", "").strip().rstrip('.').rstrip('?').rstrip('!').strip()
        if not cand or len(cand) > 240:
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

    # refuse exponentiation / pow (handled by modular engine)
    if '**' in expr or '^' in expr or 'pow' in expr:
        return None

    # allow only safe arithmetic tokens
    if not re.fullmatch(r"[0-9\+\-\*\/\(\)\.\s]+", expr):
        return None

    try:
        v = _safe_eval_expr(expr)
        return _safe_int(v)
    except Exception:
        if sp is not None:
            try:
                vv = sp.sympify(expr, locals={"C": sp.binomial, "floor": sp.floor, "ceil": sp.ceiling})
                if getattr(vv, "is_Number", False):
                    return _safe_int(vv)
            except Exception:
                pass
        return None
def solve(text: str) -> str:
    s = _clean_text(text or "")

    ordered_names = [
        "_try_modular",
        "_try_micro_arith",
        "_try_trivial_eval",
        "_try_fe_additive_bounded",
        "_try_sweets_ages",
        "_try_linear_equation",
        "_try_simple_arithmetic",
        "_try_remainder",
    ]

    fns = []
    g = globals()
    for name in ordered_names:
        fn = g.get(name)
        if callable(fn):
            fns.append(fn)

    for fn in fns:
        try:
            ans = fn(s)
            if ans is not None:
                # ensure answer stays an int (and stays small if modular applies)
                return str(int(ans))
        except Exception:
            continue

    return "0"

class Solver:
    def solve(self, text: str) -> str:
        return solve(text)

def _main():
    import sys
    txt = sys.stdin.read()
    try:
        ans = solve(txt)
    except Exception:
        ans = "0"
    sys.stdout.write(str(ans).strip() + "\n")

if __name__ == "__main__":
    _main()
