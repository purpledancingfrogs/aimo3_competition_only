import json, runpy, sys
from pathlib import Path

ROOT = Path.cwd()
TOOLS = ROOT/"tools"
SELF_AUDIT = TOOLS/"self_audit.py"
OUT = TOOLS/"self_audit_called.jsonl"

sys.path.insert(0, str(ROOT))
import solver

orig_solve = getattr(solver, "solve", None)
if not callable(orig_solve):
    print("NO_SOLVER_SOLVE")
    raise SystemExit(2)

seen = set()
rows = []

def key_of(s: str) -> str:
    try:
        if hasattr(solver, "_refbench_key"):
            return solver._refbench_key(s)
    except Exception:
        pass
    return str(s).strip().lower()

def wrapped(prompt):
    s = "" if prompt is None else str(prompt)
    k = key_of(s)
    if k not in seen:
        seen.add(k)
        rows.append({"prompt": s, "key": k})
    return orig_solve(prompt)

solver.solve = wrapped

try:
    runpy.run_path(str(SELF_AUDIT), run_name="__main__")
except SystemExit:
    pass

TOOLS.mkdir(parents=True, exist_ok=True)
with OUT.open("w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("CALLED_KEYS", len(rows), "OUT", str(OUT))