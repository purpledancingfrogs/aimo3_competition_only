from typing import List
from math import gcd
from functools import reduce

def solve_sum(nums: List[int]) -> int:
    return sum(nums)

def solve_product(nums: List[int]) -> int:
    p = 1
    for n in nums:
        p *= n
    return p

def solve_gcd(nums: List[int]) -> int:
    return reduce(gcd, nums)

def solve_difference(nums: List[int]) -> int:
    return abs(nums[0] - nums[1])

def solve_ratio(nums: List[int]) -> int:
    return nums[0] // nums[1]
