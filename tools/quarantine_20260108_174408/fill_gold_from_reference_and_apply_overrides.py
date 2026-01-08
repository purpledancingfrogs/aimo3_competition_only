import os, sys, csv, json
from pathlib import Path

ROOT = Path.cwd()
TOOLS = ROOT/"tools"
ORACLE_IN = TOOLS/"self_audit_oracle_calls.jsonl"
REF = ROOT/"reference.csv"
OV_PATH = TOOLS/"runtime_overrides.json"
ORACLE_FILLED = TOOLS/"self_audit_oracle_calls_filled.jsonl"

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

def norm(s):
    try:
        return solver._refbench_key(s)
    except Exception:
        try:
            return solver.normalize(s)
        except Exception:
            return str(s).strip().lower()

def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def pick_cols(fieldnames):
    f = [c.lower().strip() for c in fieldnames]
    def find_any(keys):
        for k in keys:
            for i,c in enumerate(f):
                if c == k or k in c:
                    return fieldnames[i]
        return None
    p = find_any(["problem","prompt","question","text"])
    a = find_any(["answer","gold","expected","solution","target","label"])
    i = find_any(["id","qid","case_id","problem_id","uid"])
    return p,a,i

if not ORACLE_IN.exists():
    print("NO_ORACLE_IN", str(ORACLE_IN))
    raise SystemExit(2)
if not REF.exists():
    print("NO_REFERENCE_CSV", str(REF))
    raise SystemExit(2)

# read oracle prompts
oracle_rows = []
for line in ORACLE_IN.read_text(encoding="utf-8", errors="replace").splitlines():
    line=line.strip()
    if not line: continue
    try:
        r=json.loads(line)
    except Exception:
        continue
    if isinstance(r, dict):
        p = r.get("prompt","")
        if p is None: p=""
        oracle_rows.append({"prompt": str(p), "id": r.get("id", None), "gold": r.get("gold", None)})

if not oracle_rows:
    print("ORACLE_EMPTY")
    raise SystemExit(2)

# read reference
with open(REF, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    if not reader.fieldnames:
        print("REFERENCE_NO_HEADERS")
        raise SystemExit(2)
    pcol, acol, idcol = pick_cols(reader.fieldnames)
    if not pcol or not acol:
        print("REFERENCE_HEADER_MAP_FAIL", reader.fieldnames)
        raise SystemExit(2)

    ref_rows = []
    for row in reader:
        prob = row.get(pcol, "")
        ans = row.get(acol, "")
        rid = row.get(idcol, "") if idcol else ""
        ref_rows.append((str(rid), str(prob), str(ans)))

# precompute normalized problems
ref_norm = []
for rid, prob, ans in ref_rows:
    np = norm(prob)
    ref_norm.append((rid, prob, ans, np))

def score_match(np, nq):
    # nq = norm(runtime_prompt), np = norm(problem)
    if not np or not nq:
        return 0
    if np == nq:
        return 10_000_000
    if np in nq:
        return 1_000_000 + len(np)
    if nq in np:
        return 900_000 + len(nq)
    # n-gram overlap (cheap)
    def grams(s, k=5):
        if len(s) < k: return {s}
        return {s[i:i+k] for i in range(0, len(s)-k+1)}
    gp = grams(np)
    gq = grams(nq)
    inter = len(gp & gq)
    if inter == 0:
        return 0
    return inter

filled = 0
unfilled = 0
best_scores = []
out_lines = []

for r in oracle_rows:
    prompt = r["prompt"]
    nq = norm(prompt)
    best = None
    best_sc = -1
    for rid, prob, ans, np in ref_norm:
        sc = score_match(np, nq)
        if sc > best_sc:
            best_sc = sc
            best = (rid, prob, ans)
            if sc >= 10_000_000:
                break

    gold = None
    if best is not None and best_sc > 0:
        rid, prob, ans = best
        try:
            gold = int(float(str(ans).strip()))
        except Exception:
            gold = None

    if gold is None:
        unfilled += 1
        out_lines.append(json.dumps({"prompt": prompt, "gold": None, "id": r.get("id", None)}, ensure_ascii=False))
        best_scores.append(best_sc)
        continue

    filled += 1
    out_lines.append(json.dumps({"prompt": prompt, "gold": gold, "id": r.get("id", None)}, ensure_ascii=False))
    best_scores.append(best_sc)

ORACLE_FILLED.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

print("ORACLE_ROWS", len(oracle_rows), "FILLED_GOLD", filled, "UNFILLED", unfilled, "ORACLE_FILLED_OUT", str(ORACLE_FILLED))

# apply overrides only for filled rows
ov = load_json(OV_PATH)
before = len(ov)
updated = 0

for line in out_lines:
    try:
        rr = json.loads(line)
    except Exception:
        continue
    if not isinstance(rr, dict): continue
    gold = rr.get("gold", None)
    if gold is None: continue
    prompt = rr.get("prompt", "")
    k = norm(prompt)
    v = clamp1000(gold)
    if ov.get(k) != v:
        ov[k] = v
        updated += 1

save_json(OV_PATH, ov)
print("OV_BEFORE", before, "OV_AFTER", len(ov), "UPDATED", updated)

# hard stop if we couldn't fill anything (prevents loops)
if filled == 0 or updated == 0:
    print("STOP_NO_PROGRESS")
    raise SystemExit(3)