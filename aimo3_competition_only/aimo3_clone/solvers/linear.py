import sympy as sp

def solve(problem: str):
    x = sp.symbols('x')
    expr = sp.sympify(problem.replace("=", "-(") + ")")
    sol = sp.solve(expr, x)
    return int(sol[0])
