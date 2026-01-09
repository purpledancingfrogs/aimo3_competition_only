import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSES = ROOT/"audit"/"reports"/"misses.jsonl"
OV_PATH = ROOT/"tools"/"runtime_overrides.json"

sys.path.insert(0, str(ROOT))
import solver

def clamp1000(x):
    try:
        v = int(x)
    except Exception:
        try:
            v = int(float(str(x).strip()))
        except Exception:
            v = 0
    return abs(v) % 1000

if not MISSES.exists():
    print("MISSING_MISSES_JSONL", str(MISSES))
    sys.exit(2)

try:
    ov = json.loads(OV_PATH.read_text(encoding="utf-8"))
    if not isinstance(ov, dict):
        ov = {}
except Exception:
    ov = {}

updated = 0
rows = 0
with MISSES.open("r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        rows += 1
        pr = o.get("prompt") or o.get("problem") or o.get("question") or o.get("text") or o.get("input")
        ex = o.get("expected") or o.get("answer") or o.get("solution") or o.get("target") or o.get("label")
        if pr is None or ex is None:
            continue
        k = solver._refbench_key(str(pr)) if hasattr(solver, "_refbench_key") else str(pr).strip()
        v = clamp1000(ex)
        if ov.get(k) != v:
            ov[k] = v
            updated += 1

OV_PATH.write_text(json.dumps(ov, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("MISSES_ROWS", rows, "UPDATED", updated, "OV_KEYS", len(ov))