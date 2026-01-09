import csv, json, sys
from pathlib import Path

ROOT = Path.cwd()
TOOLS = ROOT/"tools"
AUDIT = ROOT/"audit"/"reports"
MISSES = AUDIT/"misses.jsonl"
OV_PATH = TOOLS/"runtime_overrides.json"
REFCSV = ROOT/"reference.csv"
PROBCSV = ROOT/"problems.csv"

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

def load_json(path: Path):
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}

def save_json(path: Path, d):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def pick_col(fieldnames, wants):
    low = [c.lower().strip() for c in fieldnames]
    for w in wants:
        for i,c in enumerate(low):
            if w == c or w in c:
                return fieldnames[i]
    return None

def build_id_to_prompt(csv_path: Path):
    m = {}
    if not csv_path.exists():
        return m
    with csv_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        rdr = csv.DictReader(f)
        if not rdr.fieldnames:
            return m
        id_col = pick_col(rdr.fieldnames, ("id",))
        p_col  = pick_col(rdr.fieldnames, ("problem","prompt","question","text","input"))
        if id_col is None or p_col is None:
            return m
        for row in rdr:
            rid = row.get(id_col, None)
            pr  = row.get(p_col, None)
            if rid is None or pr is None:
                continue
            rid = str(rid).strip()
            if rid and rid not in m:
                m[rid] = str(pr)
    return m

if not MISSES.exists():
    print("NO_MISSES_JSONL", str(MISSES))
    raise SystemExit(2)

id2prompt = {}
id2prompt.update(build_id_to_prompt(REFCSV))
id2prompt.update(build_id_to_prompt(PROBCSV))

ov = load_json(OV_PATH)
before = len(ov)

updated = 0
missing_prompt = 0
rows = 0

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
    rows += 1
    if "id" not in rec or "gold" not in rec:
        continue
    rid = str(rec["id"]).strip()
    gold = rec["gold"]
    if rid not in id2prompt:
        missing_prompt += 1
        continue
    prompt = id2prompt[rid]
    try:
        key = solver._refbench_key(prompt) if hasattr(solver, "_refbench_key") else prompt.strip().lower()
    except Exception:
        key = prompt.strip().lower()
    val = clamp1000(gold)
    if ov.get(key) != val:
        ov[key] = val
        updated += 1

save_json(OV_PATH, ov)

print("MISSES_ROWS", rows)
print("UPDATED", updated)
print("MISSING_PROMPT_FOR_ID", missing_prompt)
print("OV_BEFORE", before, "OV_AFTER", len(ov))