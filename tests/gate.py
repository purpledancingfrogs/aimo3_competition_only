import re
from pathlib import Path

def file_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def main():
    bad = []

    self_path = Path("tests") / "gate.py"

    # determinism scan: reject actual randomness imports/usages
    for p in Path(".").rglob("*.py"):
        ps = str(p).replace("\\", "/")
        if ps.startswith(".venv/") or ps.startswith("venv/") or ps.startswith("__pycache__/") or ps.startswith(".git/"):
            continue
        if p == self_path:
            continue

        t = file_text(p)

        if re.search(r"(?m)^\s*import\s+random\b", t) or re.search(r"(?m)^\s*from\s+random\s+import\b", t):
            bad.append(f"RANDOM_IMPORT:{p}")

        # avoid matching this scanner by not embedding "random.seed(" as a literal anywhere
        if ("random" + ".seed(") in t or ("numpy" + ".random") in t:
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
