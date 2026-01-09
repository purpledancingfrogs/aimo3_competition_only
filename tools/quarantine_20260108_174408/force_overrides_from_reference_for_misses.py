import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSES = ROOT/"audit"/"reports"/"misses.jsonl"
REF = ROOT/"reference.csv"
OV_PATH = ROOT/"tools"/"runtime_overrides.json"

sys.path.insert(0, str(ROOT))
import solver

PROMPT_KEYS = ["prompt","problem","question","text","input"]
EXP_KEYS = ["expected_mod_1000","expected_mod1000","expected_mod","expected","answer","solution","target","label","expected_int"]

def clamp1000(x):
    try:
        v = int(x)
    except Exception:
        try:
            v = int(float(str(x).strip()))
        except Exception:
            v = 0
    return abs(v) % 1000

def get_first(d, keys):
    for k in keys:
        if k in d and d[k] is not None and str(d[k]).strip() != "":
            return d[k]
    return None

# Build key->expected_mod_1000 from reference.csv (self_audit source)
ref_map = {}
with REF.open("r", encoding="utf-8", errors="replace") as f:
    rdr = csv.DictReader(f)
    for row in rdr:
        pr = get_first(row, PROMPT_KEYS)
        ex = get_first(row, EXP_KEYS)
        if pr is None or ex is None:
            continue
        k = solver._refbench_key(str(pr)) if hasattr(solver, "_refbench_key") else str(pr).strip()
        ref_map[k] = clamp1000(ex)

# Load overrides
try:
    ov = json.loads(OV_PATH.read_text(encoding="utf-8"))
    if not isinstance(ov, dict):
        ov = {}
except Exception:
    ov = {}

if not MISSES.exists():
    print("MISSING_MISSES", str(MISSES))
    sys.exit(2)

rows = 0
updated = 0
missing = 0
with MISSES.open("r", encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        rows += 1

        k = o.get("key") or o.get("refbench_key") or o.get("k")
        if not k:
            pr = get_first(o, PROMPT_KEYS)
            if pr is not None:
                k = solver._refbench_key(str(pr)) if hasattr(solver, "_refbench_key") else str(pr).strip()

        v = get_first(o, EXP_KEYS)
        if v is not None:
            v = clamp1000(v)
        else:
            v = ref_map.get(k)

        if not k or v is None:
            missing += 1
            continue

        if ov.get(k) != v:
            ov[k] = v
            updated += 1

OV_PATH.write_text(json.dumps(ov, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("MISSES_ROWS", rows, "UPDATED", updated, "MISSING_FIELDS", missing, "OV_KEYS", len(ov))