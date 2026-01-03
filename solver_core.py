# Replace solver_core.py with arithmetic-first parsing (highest ROI)

import re
from fractions import Fraction
from solver_modules.arithmetic import (
    solve_sum, solve_product, solve_gcd,
    solve_difference, solve_ratio, solve_lcm
)

def _nums(s: str):
    return [Fraction(x) for x in re.findall(r"-?\d+(?:/\d+)?", s)]

def dss_omega_solver(problem: str) -> int:
    p = problem.lower()
    p = p.replace("plus","+").replace("minus","-").replace("times","*").replace("divided by","/")
    p = re.sub(r"[^\w\d\+\-\*/=\/ ]","",p)

    nums = _nums(p)

    if "=" in p and "x" in p:
        left,right = p.split("=")
        rhs = nums[-1]
        a = Fraction(1)
        b = Fraction(0)
        m = re.search(r"(-?\d*)x", left)
        if m:
            a = Fraction(m.group(1)) if m.group(1) not in ("","-") else Fraction(-1 if m.group(1)=="-" else 1)
        others = _nums(left.replace("x",""))
        if others: b = others[0]
        return int((rhs-b)/a)

    if "+" in p and nums:
        return int(sum(nums))
    if "*" in p:
        r=Fraction(1)
        for n in nums: r*=n
        return int(r)
    if "gcd" in p:
        return solve_gcd([int(n) for n in nums])
    if "lcm" in p:
        return solve_lcm([int(n) for n in nums])
    if "-" in p and len(nums)>=2:
        return int(nums[0]-nums[1])
    if "/" in p and len(nums)>=2:
        return int(nums[0]/nums[1])

    return int(nums[0]) if nums else 0
