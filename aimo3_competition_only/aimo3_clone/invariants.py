import sympy as sp

def extract(problem: str):
    x = sp.symbols('x')
    expr = sp.sympify(problem.replace("=", "-(") + ")")

    degree = sp.degree(expr, x)
    if degree is not None:
        degree = int(degree)

    invariants = {
        "degree": degree,
        "domain": "Z",
        "symmetry": "reflection" if expr.subs(x, -x) == expr else "none",
        "bounded": False,
        "dimensional": False
    }
    return invariants

if __name__ == "__main__":
    print(extract("x^2-4=0"))
