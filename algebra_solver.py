import sympy as sp

def solve_algebra(problem: str):
    try:
        x = sp.symbols("x")
        eq = sp.sympify(problem.replace("=", "-(") + ")")
        sol = sp.solve(eq, x)
        return sol[0] if sol else None
    except:
        return None
