from router import solve as route_solve
from sympy import Integer, Rational, Expr

def _normalize(obj):
    if isinstance(obj, Integer):
        return int(obj)
    if isinstance(obj, Rational):
        return float(obj)
    if isinstance(obj, Expr):
        try:
            return int(obj)
        except Exception:
            try:
                return float(obj)
            except Exception:
                return str(obj)
    if isinstance(obj, dict):
        return {k: _normalize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize(v) for v in obj]
    return obj

def dss_omega_solver(problem):
    result = route_solve(problem)
    return _normalize(result)
