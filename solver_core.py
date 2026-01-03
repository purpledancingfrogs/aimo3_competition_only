from __future__ import annotations
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from parser import parse_problem, Parsed

# Optional: sympy path (safe fallback if unavailable)
_SYMPY_OK = False
try:
    import sympy as sp
    from sympy.parsing.sympy_parser import (
        parse_expr,
        standard_transformations,
        implicit_multiplication_application,
        convert_xor,
    )
    _SYMPY_OK = True
    _TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)
except Exception:
    sp = None  # type: ignore

_INT = re.compile(r"[-+]?\d+")

def _ints(s: str) -> List[int]:
    return [int(x) for x in _INT.findall(s)]

def _safe_int(x: Any) -> Optional[int]:
    try:
        if x is None:
            return None
        if isinstance(x, bool):
            return int(x)
        if isinstance(x, int):
            return x
        if isinstance(x, float) and abs(x - round(x)) < 1e-9:
            return int(round(x))
        # sympy Integer / Rational
        if _SYMPY_OK:
            if isinstance(x, sp.Integer):
                return int(x)
            if isinstance(x, sp.Rational):
                if x.q != 0 and x.p % x.q == 0:
                    return int(x.p // x.q)
        return int(str(x).strip())
    except Exception:
        return None

def solve_gcd(nums: List[int]) -> int:
    g = 0
    for n in nums:
        g = math.gcd(g, abs(n))
    return g

def solve_lcm(nums: List[int]) -> int:
    def lcm(a: int, b: int) -> int:
        return 0 if a == 0 or b == 0 else abs(a // math.gcd(a, b) * b)
    v = 1
    for n in nums:
        v = lcm(v, n)
    return v

def solve_sum(nums: List[int]) -> int:
    return sum(nums)

def solve_product(nums: List[int]) -> int:
    p = 1
    for n in nums:
        p *= n
    return p

def solve_mod(nums: List[int]) -> Optional[int]:
    # expects "... a mod m ..." or "remainder when a is divided by m"
    if len(nums) >= 2:
        a, m = nums[0], nums[1]
        if m == 0:
            return None
        return a % m
    return None

def _sympy_try_eval(parsed: Parsed) -> Optional[int]:
    if not _SYMPY_OK:
        return None

    # Prefer latex chunk if present; else attempt expression scrape from text.
    candidate = parsed.latex.strip()
    if not candidate:
        # try to isolate an expression-like substring after "compute"/"evaluate"/"find"
        t = parsed.text
        # crude: take after first keyword
        for kw in ("compute", "evaluate", "simplify", "find", "determine"):
            idx = t.find(kw)
            if idx >= 0:
                candidate = t[idx + len(kw):].strip(" :;.")
                break
        if not candidate:
            candidate = t

    # sanitize common words
    candidate = candidate.replace("equals", "=").replace("= ?", "=").replace("=?", "=")
    candidate = candidate.replace("−", "-").replace("^", "**")

    # If an equation exists, try solving for a single variable.
    if "=" in candidate:
        parts = candidate.split("=")
        if len(parts) == 2:
            left, right = parts[0].strip(), parts[1].strip()
            # choose a likely variable
            vars_found = sorted(set(re.findall(r"[a-zA-Z]", left + right)))
            if vars_found:
                x = sp.Symbol(vars_found[0])
                try:
                    L = parse_expr(left, transformations=_TRANSFORMS, evaluate=True)
                    R = parse_expr(right, transformations=_TRANSFORMS, evaluate=True)
                    sol = sp.solve(sp.Eq(L, R), x, dict=True)
                    if sol:
                        v = sol[0].get(x, None)
                        return _safe_int(v)
                except Exception:
                    pass
        return None

    # Otherwise, attempt direct numeric evaluation.
    try:
        expr = parse_expr(candidate, transformations=_TRANSFORMS, evaluate=True)
        expr = sp.simplify(expr)
        return _safe_int(expr)
    except Exception:
        return None

def _heuristic_dispatch(parsed: Parsed) -> Optional[int]:
    nums = parsed.nums
    f = parsed.flags
    t = parsed.text

    if f.get("has_gcd") and len(nums) >= 2:
        return solve_gcd(nums)

    if f.get("has_lcm") and len(nums) >= 2:
        return solve_lcm(nums)

    if f.get("has_sum") and len(nums) >= 1:
        return solve_sum(nums)

    if f.get("has_product") and len(nums) >= 1:
        return solve_product(nums)

    if f.get("has_mod") and len(nums) >= 2:
        v = solve_mod(nums)
        if v is not None:
            return v

    # explicit a + b in text (two numbers)
    if f.get("has_plus") and len(nums) == 2:
        return nums[0] + nums[1]

    # "difference between a and b"
    if f.get("has_difference") and len(nums) >= 2:
        return abs(nums[0] - nums[1])

    # ratio a/b with integer result
    if f.get("has_ratio") and len(nums) >= 2 and nums[1] != 0:
        q = nums[0] / nums[1]
        if abs(q - round(q)) < 1e-9:
            return int(round(q))

    return None

def dss_omega_solver(problem: str) -> int:
    """
    Deterministic solver.
    Contract: returns an integer (fallback 0) with no network, no randomness.
    """
    parsed = parse_problem(problem)

    # 1) sympy-first when possible (broad coverage for arithmetic/algebra)
    v = _sympy_try_eval(parsed)
    if v is not None:
        return int(v)

    # 2) controlled heuristics
    v = _heuristic_dispatch(parsed)
    if v is not None:
        return int(v)

    # 3) conservative fallback (audit-safe)
    return 0
