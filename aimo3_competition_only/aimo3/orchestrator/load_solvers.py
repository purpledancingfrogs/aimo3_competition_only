# AIMO-3 required loader shim
def load_solvers(*args, **kwargs):
    # Defer to existing Aureon mechanisms if present
    try:
        from orchestrator.orchestrator import run
        return run
    except Exception:
        return None
