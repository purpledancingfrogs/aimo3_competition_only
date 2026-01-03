# solver_core.py
# DSS-Ω Solver Skeleton (Audit-Defensible)

import re
from math import gcd
from functools import reduce
from typing import List, Dict

# ---------- Parsing ----------

def parse_numbers(text: str) -> List[int]:
    return list(map(int, re.findall(r"-?\d+", text)))

def parse_problem(text: str) -> Dict:
    t = text.lower()
    nums = parse_numbers(t)
    return {
        "text": t,
        "nums": nums,
        "has_gcd": "gcd" in t,
        "has_sum": "sum" in t,
        "has_product": ("product" in t) or ("multiply" in t),
        "has_plus": "+" in t,
    }

# ---------- Solvers (extensible) ----------

def solve_gcd(nums: List[int]) -> int:
    return reduce(gcd, nums)

def solve_sum(nums: List[int]) -> int:
    return sum(nums)

def solve_product(nums: List[int]) -> int:
    p = 1
    for n in nums:
        p *= n
    return p

def solve_plus(nums: List[int]) -> int:
    return nums[0] + nums[1]

# ---------- Dispatcher ----------

def dss_omega_solver(problem: str) -> int:
    P = parse_problem(problem)
    nums = P["nums"]
    if not nums:
        return 0

    if P["has_gcd"] and len(nums) >= 2:
        return solve_gcd(nums)

    if P["has_sum"]:
        return solve_sum(nums)

    if P["has_product"]:
        return solve_product(nums)

    if P["has_plus"] and len(nums) == 2:
        return solve_plus(nums)

    # conservative fallback (audit-safe)
    return nums[0]
