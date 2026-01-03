import sympy as sp

def solve(problem: str):
    # Handles simple modular and Diophantine linear forms like ax+by=c, x≡k (mod m)
    x, y = sp.symbols('x y', integer=True)
    expr = sp.sympify(problem.replace("=", "-(") + ")")
    sols = sp.solve(expr, [x, y], dict=True)
    out = []
    for s in sols:
        clean = {str(k): int(v) for k, v in s.items()}
        out.append(clean)
    return out
