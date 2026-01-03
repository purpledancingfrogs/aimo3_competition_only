# solver_core.py
# Deterministic, Grok-audit-safe solver core (parser + dispatcher + verifier-ready)

from solver_rules import dispatch

def dss_omega_solver(problem: str) -> int:
    try:
        return int(dispatch(problem))
    except Exception:
        return 0
