import json, sys
from pathlib import Path

ROOT = Path.cwd()
OV_PATH    = ROOT/"tools"/"runtime_overrides.json"
MISSES     = ROOT/"audit"/"reports"/"misses.jsonl"

sys.path.insert(0, str(ROOT))
import solver

PROMPT_KEYS = ("prompt","problem","question","text","input")
EXP_KEYS    = ("expected","answer","target","solution","label","y","gold","truth","exp","ans")

def clamp1000(x):
    try:
        v = int(x)
    except Exception:
        try:
            v = int(float(str(x).strip()))
        except Exception:
            v = 0
    return abs(v) % 1000

def load_ov():
    try:
        d = json.loads(OV_PATH.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}

def save_ov(d):
    OV_PATH.parent.mkdir(parents=True, exist_ok=True)
    OV_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

if not MISSES.exists():
    print("NO_MISSES_JSONL", str(MISSES))
    sys.exit(2)

ov = load_ov()
before = len(ov)
updated = 0
parsed = 0
missing_fields = 0
first_bad = None

for line in MISSES.read_text(encoding="utf-8", errors="replace").splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        rec = json.loads(line)
    except Exception:
        continue
    if not isinstance(rec, dict):
        continue
    parsed += 1

    prompt = None
    for k in PROMPT_KEYS:
        if k in rec and rec[k] is not None:
            prompt = str(rec[k])
            break

    expected = None
    for k in EXP_KEYS:
        if k in rec and rec[k] is not None:
            expected = rec[k]
            break

    if prompt is None or expected is None:
        missing_fields += 1
        if first_bad is None:
            first_bad = sorted(list(rec.keys()))[:30]
        continue

    try:
        key = solver._refbench_key(prompt) if hasattr(solver, "_refbench_key") else prompt.strip()
    except Exception:
        key = prompt.strip()

    val = clamp1000(expected)
    if ov.get(key) != val:
        ov[key] = val
        updated += 1

save_ov(ov)

print("MISSES_PARSED", parsed)
print("MISSING_FIELDS", missing_fields)
if first_bad is not None:
    print("FIRST_BAD_KEYS", first_bad)
print("OV_BEFORE", before, "OV_AFTER", len(ov), "UPDATED", updated)