from .arithmetic import *

DISPATCH = {
    'sum': solve_sum,
    'difference': solve_difference,
    'product': solve_product,
    'ratio': solve_ratio,
    'gcd': solve_gcd,
    'lcm': solve_lcm,
}

def dispatch(op, a, b):
    return DISPATCH[op](a, b)

def try_arithmetic(op, a, b):
    try:
        return dispatch(op, a, b)
    except Exception:
        return None
