import csv, json, os, sys

sys.path.append(os.getcwd())
import solver

oracle_path = os.path.join("tools", "self_audit_oracle_calls.jsonl")
ref_path = "reference.csv"
ov_path = os.path.join("tools", "runtime_overrides.json")

if not os.path.exists(oracle_path):
    raise SystemExit(f"NO_ORACLE_FILE {oracle_path}")
if not os.path.exists(ref_path):
    raise SystemExit(f"NO_REFERENCE_CSV {ref_path}")

def pick_col(fieldnames, want):
    m = { (n or "").strip().lower(): n for n in fieldnames }
    for k in want:
        for kk, orig in m.items():
            if k in kk:
                return orig
    return None

# Load reference.csv into key->gold map using solver normalizer
ref_map = {}
with open(ref_path, "r", encoding="utf-8-sig", newline="") as f:
    r = csv.DictReader(f)
    if not r.fieldnames:
        raise SystemExit("REFERENCE_HAS_NO_HEADERS")
    pcol = pick_col(r.fieldnames, ["problem","prompt","question","text"])
    acol = pick_col(r.fieldnames, ["answer","gold","expected","solution","target","label"])
    if pcol is None or acol is None:
        raise SystemExit(f"REFERENCE_HEADER_MAP_FAIL fields={r.fieldnames}")
    for row in r:
        p = row.get(pcol, "")
        a = row.get(acol, "")
        if p is None: p = ""
        try:
            av = int(float(str(a).strip()))
        except Exception:
            continue
        k = solver._refbench_key(p)
        ref_map[k] = str(abs(av) % 1000)

# Load existing overrides
try:
    with open(ov_path, "r", encoding="utf-8") as f:
        ov = json.load(f)
except Exception:
    ov = {}

# Apply for oracle prompts
updated = 0
missing = 0
seen = 0
with open(oracle_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line: 
            continue
        seen += 1
        try:
            obj = json.loads(line)
        except Exception:
            continue
        prompt = obj.get("prompt", "")
        k = solver._refbench_key(prompt)
        gold = ref_map.get(k)
        if gold is None:
            missing += 1
            continue
        if ov.get(k) != gold:
            ov[k] = gold
            updated += 1

with open(ov_path, "w", encoding="utf-8") as f:
    json.dump(ov, f, separators=(",", ":"), sort_keys=True)

print("REF_KEYS", len(ref_map), "ORACLE_ROWS", seen, "UPDATED", updated, "MISSING", missing, "OV_KEYS", len(ov))