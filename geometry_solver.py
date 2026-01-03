import re
from fractions import Fraction
import math

def solve_geometry(problem: str):
    p = problem.lower()
    nums = list(map(Fraction, re.findall(r"\d+", p)))

    # triangle area
    if "triangle" in p and "area" in p and len(nums) >= 2:
        base, height = nums[0], nums[1]
        return Fraction(base * height, 2)

    # square area
    if "square" in p and "area" in p and nums:
        return nums[0] * nums[0]

    # circle area (symbolic pi)
    if "circle" in p and "area" in p and nums:
        r = nums[0]
        return f"{r*r}*pi"

    return None
