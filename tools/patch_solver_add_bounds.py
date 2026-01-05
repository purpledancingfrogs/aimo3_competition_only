from pathlib import Path

MARK = "AUREON_BOUNDS_VETO_v1"

def main():
    p = Path("solver.py")
    if not p.exists():
        raise SystemExit("MISSING:solver.py")
    s = p.read_text(encoding="utf-8", errors="strict")

    if MARK in s:
        print("PATCH_ALREADY_PRESENT")
        return

    patch = f"""

# {MARK}
try:
    from bounds import run_guarded
    _AUREON__orig = None
    if "Solver" in globals() and hasattr(Solver, "solve"):
        _AUREON__orig = Solver.solve
        def _AUREON__wrapped(self, text):
            return run_guarded(lambda g: _AUREON__orig(self, text), fallback=0)
        Solver.solve = _AUREON__wrapped
except Exception:
    pass
"""

    s2 = s.rstrip() + "\n" + patch
    p.write_text(s2, encoding="utf-8")
    print("PATCH_OK")

if __name__ == "__main__":
    main()
