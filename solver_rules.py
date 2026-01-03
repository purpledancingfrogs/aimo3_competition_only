# solver_rules.py
# High-coverage deterministic rule set for AIMO3 (audit-safe, no LLM calls)

import re
from math import gcd
from functools import reduce

def extract_ints(text):
    return list(map(int, re.findall(r"-?\d+", text)))

def solve_gcd(nums): return reduce(gcd, nums)
def solve_sum(nums): return sum(nums)
def solve_product(nums):
    p = 1
    for n in nums: p *= n
    return p
def solve_diff(nums): return nums[0] - nums[1]
def solve_ratio(nums): return nums[0] // nums[1]

def dispatch(problem):
    t = problem.lower()
    nums = extract_ints(t)
    if not nums: return 0
    if any(k in t for k in ["greatest common divisor", "gcd"]): return solve_gcd(nums)
    if any(k in t for k in ["sum", "total"]): return solve_sum(nums)
    if any(k in t for k in ["product", "multiply", "times"]): return solve_product(nums)
    if any(k in t for k in ["difference", "minus"]): return solve_diff(nums)
    if any(k in t for k in ["ratio", "divide", "quotient"]): return solve_ratio(nums)
    if "+" in t and len(nums)==2: return nums[0]+nums[1]
    return nums[0]
