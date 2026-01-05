import re, sys
from pathlib import Path

def file_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def main():
    # determinism scan: reject obvious randomness
    bad = []
    for p in Path(".").rglob("*.py"):
        if any(x in str(p).lower() for x in [r"\.venv", r"\__pycache__", "/.venv", "/__pycache__"]):
            continue
        t = file_text(p)
        if re.search(r"(?m)^\s*import\s+random\b", t) or re.search(r"(?m)^\s*from\s+random\s+import\b", t):
            bad.append(f"RANDOM_IMPORT:{p}")
        if "numpy.random" in t or "random.seed(" in t:
            bad.append(f"RANDOM_USAGE:{p}")

    # bounds veto must be present
    sp = Path("solver.py")
    if not sp.exists():
        bad.append("MISSING:solver.py")
    else:
        if "AUREON_BOUNDS_VETO_v1" not in file_text(sp):
            bad.append("MISSING_BOUNDS_PATCH:solver.py")

    # gateway must exist
    gw = Path("kaggle_evaluation") / "aimo_3_gateway.py"
    if not gw.exists():
        bad.append("MISSING_GATEWAY:kaggle_evaluation/aimo_3_gateway.py")

    if bad:
        print("\n".join(bad))
        raise SystemExit("GATE_FAIL")

    print("GATE_OK")

if __name__ == "__main__":
    main()
