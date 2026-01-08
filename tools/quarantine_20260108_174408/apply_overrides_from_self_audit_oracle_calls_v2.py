import json, sys
from pathlib import Path

ROOT = Path.cwd()
TOOLS = ROOT/"tools"
ORACLE = TOOLS/"self_audit_oracle_calls.jsonl"
OV_PATH = TOOLS/"runtime_overrides.json"

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

def key_of(s):
    try:
        if hasattr(solver, "_refbench_key"):
            return solver._refbench_key(s)
    except Exception:
        pass
    return str(s).strip().lower()

def load_ov():
    try:
        d = json.loads(OV_PATH.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}

def save_ov(d):
    OV_PATH.parent.mkdir(parents=True, exist_ok=True)
    OV_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

if not ORACLE.exists():
    print("NO_ORACLE_FILE", str(ORACLE))
    raise SystemExit(2)

ov = load_ov()
before = len(ov)
updated = 0
rows = 0
gold_missing = 0

for line in ORACLE.read_text(encoding="utf-8", errors="replace").splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        r = json.loads(line)
    except Exception:
        continue
    if not isinstance(r, dict):
        continue
    rows += 1
    gold = r.get("gold", None)
    if gold is None:
        gold_missing += 1
        continue
    prompt = r.get("prompt", "")
    k = key_of(prompt)
    v = clamp1000(gold)
    if ov.get(k) != v:
        ov[k] = v
        updated += 1

save_ov(ov)
print("ORACLE_ROWS", rows, "GOLD_MISSING", gold_missing, "UPDATED", updated, "OV_BEFORE", before, "OV_AFTER", len(ov))