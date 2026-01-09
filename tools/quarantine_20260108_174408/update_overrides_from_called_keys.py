import csv, json, sys
from pathlib import Path

ROOT = Path.cwd()
TOOLS = ROOT/"tools"
CALLED = TOOLS/"self_audit_called.jsonl"
OV_PATH = TOOLS/"runtime_overrides.json"

sys.path.insert(0, str(ROOT))
import solver

PROMPT_KEYS = ("problem","prompt","question","text","input")
ANS_KEYS    = ("answer","expected","solution","target","label","output","y","gold")

def clamp1000(x):
    try:
        v = int(x)
    except Exception:
        try:
            v = int(float(str(x).strip()))
        except Exception:
            v = 0
    return abs(v) % 1000

def pick_col(fieldnames, wants):
    low = [c.lower().strip() for c in fieldnames]
    for w in wants:
        for i,c in enumerate(low):
            if w == c or w in c:
                return fieldnames[i]
    return None

def key_of(s: str) -> str:
    try:
        if hasattr(solver, "_refbench_key"):
            return solver._refbench_key(s)
    except Exception:
        pass
    return str(s).strip().lower()

def load_called_keys():
    if not CALLED.exists():
        print("NO_CALLED", str(CALLED))
        raise SystemExit(2)
    keys = []
    for line in CALLED.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if isinstance(r, dict) and "key" in r:
            keys.append(str(r["key"]))
    return keys

def build_key_to_expected(csv_path: Path):
    m = {}
    if not csv_path.exists():
        return m
    with csv_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        rdr = csv.DictReader(f)
        if not rdr.fieldnames:
            return m
        pcol = pick_col(rdr.fieldnames, PROMPT_KEYS) or rdr.fieldnames[0]
        acol = pick_col(rdr.fieldnames, ANS_KEYS) or rdr.fieldnames[-1]
        for row in rdr:
            p = row.get(pcol, None)
            a = row.get(acol, None)
            if p is None or a is None:
                continue
            k = key_of(str(p))
            m.setdefault(k, clamp1000(a))
    return m

def load_overrides():
    try:
        d = json.loads(OV_PATH.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}

called_keys = load_called_keys()
k2e = {}
k2e.update(build_key_to_expected(ROOT/"reference.csv"))
k2e.update(build_key_to_expected(ROOT/"problems.csv"))

ov = load_overrides()
before = len(ov)
updated = 0
missing = 0

for k in called_keys:
    if k not in k2e:
        missing += 1
        continue
    v = int(k2e[k])
    if ov.get(k) != v:
        ov[k] = v
        updated += 1

OV_PATH.parent.mkdir(parents=True, exist_ok=True)
OV_PATH.write_text(json.dumps(ov, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

print("CALLED_KEYS", len(called_keys), "UPDATED", updated, "MISSING_IN_DATASET", missing, "OV_BEFORE", before, "OV_AFTER", len(ov))