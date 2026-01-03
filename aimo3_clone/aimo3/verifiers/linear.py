import sympy as sp

def verify(problem: str, answer: int) -> bool:
    x = sp.symbols('x')
    expr = sp.sympify(problem.replace("=", "-(") + ")")
    return bool(expr.subs(x, answer) == 0)
