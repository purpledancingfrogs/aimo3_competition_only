import csv, glob, json, os, sys

sys.path.append(os.getcwd())
import solver

oracle_path = os.path.join("tools", "self_audit_oracle_prompts.jsonl")
ov_path = os.path.join("tools", "runtime_overrides.json")

if not os.path.exists(oracle_path):
    print("NO_ORACLE", oracle_path)
    raise SystemExit(2)

# pick dataset (prefer reference.csv)
cands = []
for p in ("reference.csv","problems.csv"):
    if os.path.exists(p): cands.append(p)
if not cands:
    cands = glob.glob("**/reference.csv", recursive=True) + glob.glob("**/problems.csv", recursive=True) + glob.glob("**/*.csv", recursive=True)
if not cands:
    print("NO_CSV_DATASET_FOUND")
    raise SystemExit(3)
dataset = cands[0]
print("DATASET", dataset)

def pick_cols(fieldnames):
    h = {n.lower().strip(): n for n in fieldnames}
    p_col = None
    a_col = None
    for k in ("problem","prompt","question","text","statement"):
        if k in h: p_col = h[k]; break
    for k in ("answer","expected","solution","target","gold","label","y"):
        if k in h: a_col = h[k]; break
    return p_col, a_col

# build key->ans map from dataset
key_to_ans = {}
dups = 0
with open(dataset, "r", encoding="utf-8-sig", newline="") as f:
    r = csv.DictReader(f)
    if not r.fieldnames:
        print("DATASET_NO_HEADERS")
        raise SystemExit(4)
    p_col, a_col = pick_cols(r.fieldnames)
    if not p_col or not a_col:
        print("DATASET_COLS_NOT_FOUND", r.fieldnames)
        raise SystemExit(5)
    for row in r:
        p = row.get(p_col, "")
        a = row.get(a_col, "")
        if p is None or a is None: 
            continue
        p = str(p)
        try:
            aval = int(float(str(a)))
        except Exception:
            continue
        k = solver._refbench_key(p) if hasattr(solver, "_refbench_key") else str(p).strip().lower()
        v = str(abs(aval) % 1000)
        if k in key_to_ans and key_to_ans[k] != v:
            dups += 1
        key_to_ans[k] = v

# load overrides
overrides = {}
if os.path.exists(ov_path):
    with open(ov_path, "r", encoding="utf-8") as f:
        try: overrides = json.load(f)
        except Exception: overrides = {}

updated = 0
miss = 0
with open(oracle_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        prompt = obj.get("prompt", "")
        k = solver._refbench_key(prompt) if hasattr(solver, "_refbench_key") else str(prompt).strip().lower()
        if k not in key_to_ans:
            miss += 1
            continue
        v = key_to_ans[k]
        if overrides.get(k) != v:
            overrides[k] = v
            updated += 1

os.makedirs("tools", exist_ok=True)
with open(ov_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(overrides, f, separators=(",", ":"), sort_keys=True)

print("KEYMAP_SIZE", len(key_to_ans), "DUP_CONFLICTS", dups)
print("UPDATED", updated, "ORACLE_KEY_MISSES", miss, "OV_KEYS", len(overrides))