import sympy as sp

def verify(problem: str, answers):
    x = sp.symbols('x')
    expr = sp.sympify(problem.replace("=", "-(") + ")")
    for a in answers:
        if expr.subs(x, a) != 0:
            return False
    return True
