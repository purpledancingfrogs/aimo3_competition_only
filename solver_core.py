# solver_core.py
# DSS-Ω deterministic solver core
# Audit-safe: rule-based, no randomness, no learning

import re
from typing import List
from solver_modules.arithmetic import (
    solve_sum,
    solve_product,
    solve_gcd,
    solve_difference,
    solve_ratio,
)

# ---------------- helpers ----------------

def solve_lcm(nums: List[int]) -> int:
    from math import gcd
    from functools import reduce
    def lcm(a, b): return a * b // gcd(a, b)
    return reduce(lcm, nums)

def solve_power(nums: List[int]) -> int:
    return nums[0] ** nums[1]

def extract_ints(s: str) -> List[int]:
    return list(map(int, re.findall(r'-?\d+', s)))

def normalize(p: str) -> str:
    p = p.lower().strip()
    p = p.replace("?", "")
    p = p.replace("plus", "+")
    p = p.replace("minus", "-")
    p = p.replace("times", "*")
    p = p.replace("multiplied by", "*")
    p = p.replace("divided by", "/")
    p = p.replace("twice", "2 *")
    p = p.replace("double", "2 *")
    p = p.replace("half", "/ 2")
    return p

# ---------------- linear equations ----------------

def solve_linear_equation(p: str) -> int:
    # supports: x + a = b, a + x = b, ax = b, a*x = b
    p = p.replace("solve:", "").strip()
    lhs, rhs = p.split("=")
    rhs = int(rhs.strip())

    lhs = lhs.replace(" ", "")
    if lhs == "x":
        return rhs

    if lhs.startswith("x+"):
        return rhs - int(lhs[2:])
    if lhs.endswith("+x"):
        return rhs - int(lhs[:-2])
    if lhs.startswith("x-"):
        return rhs + int(lhs[2:])
    if lhs.endswith("-x"):
        return int(lhs[:-2]) - rhs
    if lhs.endswith("x"):
        return rhs // int(lhs[:-1])
    if lhs.startswith("x*"):
        return rhs // int(lhs[2:])
    if "*" in lhs and "x" in lhs:
        a = int(lhs.replace("x*", "").replace("*x", ""))
        return rhs // a

    raise ValueError("Unsupported linear equation")

# ---------------- dispatcher ----------------

def dss_omega_solver(problem: str) -> int:
    p = normalize(problem)

    if p.startswith("solve"):
        p = p.replace("solve:", "solve").replace("solve", "").strip()
        return solve_linear_equation(p)

    nums = extract_ints(p)

    if "sum of" in p or p.startswith("compute the sum"):
        return solve_sum(nums)
    if "product of" in p:
        return solve_product(nums)
    if "gcd" in p:
        return solve_gcd(nums)
    if "lcm" in p:
        return solve_lcm(nums)
    if "difference" in p:
        return solve_difference(nums)
    if "ratio" in p:
        return solve_ratio(nums)
    if "mod" in p:
        return nums[0] % nums[1]
    if "^" in p or "power" in p:
        return solve_power(nums)

        # Safe fallback: try eval of sanitized arithmetic
    try:
        expr = re.sub(r"[^0-9\+\-\*/\(\)\s]", "", p)
        if expr.strip():
            return int(eval(expr))
    except:
        pass
    return 0
