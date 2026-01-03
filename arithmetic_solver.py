import re
from fractions import Fraction

def solve_arithmetic(problem: str):
    try:
        expr = re.sub(r"[^0-9\+\-\*\/\(\)]", "", problem)
        return Fraction(eval(expr))
    except:
        return None
