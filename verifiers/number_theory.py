import sympy as sp

def verify(problem: str, solutions):
    x, y = sp.symbols('x y', integer=True)
    expr = sp.sympify(problem.replace("=", "-(") + ")")
    for sol in solutions:
        subs = {x: sol.get("x"), y: sol.get("y")}
        if expr.subs(subs) != 0:
            return False
    return True
