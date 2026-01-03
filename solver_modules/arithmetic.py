from math import gcd
from fractions import Fraction

def solve_sum(a,b): return a+b
def solve_difference(a,b): return a-b
def solve_product(a,b): return a*b
def solve_ratio(a,b): return Fraction(a,b)
def solve_gcd(a,b): return gcd(a,b)
def solve_lcm(a,b): return abs(a*b)//gcd(a,b)
