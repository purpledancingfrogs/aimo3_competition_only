import re

def solve_equation(expr: str) -> int:
    expr = expr.replace(' ', '')
    if '=' not in expr:
        return 0
    lhs, rhs = expr.split('=')
    try:
        return int(eval(lhs) - eval(rhs))
    except Exception:
        return 0
