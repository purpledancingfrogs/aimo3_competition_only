import sympy as sp

def solve(problem: str):
    x = sp.symbols('x')
    expr = sp.sympify(problem.replace("=", "-(") + ")")
    sols = sp.solve(expr, x)
    out = []
    for s in sols:
        if s.is_real:
            out.append(float(s) if s % 1 else int(s))
    return out
