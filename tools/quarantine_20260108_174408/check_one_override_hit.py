import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
MISSES = ROOT/"audit"/"reports"/"misses.jsonl"
OV_PATH = ROOT/"tools"/"runtime_overrides.json"
sys.path.insert(0, str(ROOT))
import solver

miss = None
for line in MISSES.read_text(encoding="utf-8").splitlines():
    line=line.strip()
    if not line: 
        continue
    miss = json.loads(line); break

pr = miss.get("prompt") or miss.get("problem") or miss.get("question") or miss.get("text") or miss.get("input")
ex = miss.get("expected") or miss.get("answer") or miss.get("solution") or miss.get("target") or miss.get("label")
ov = json.loads(OV_PATH.read_text(encoding="utf-8"))
key = solver._refbench_key(str(pr)) if hasattr(solver,"_refbench_key") else str(pr).strip()
print("KEY_IN_OV", key in ov)
print("OV_VAL", ov.get(key))
try:
    got = solver.solve(str(pr))
except Exception as e:
    got = f"EXC:{type(e).__name__}:{e}"
print("SOLVE_GOT", got)
print("EXPECTED_RAW", ex)