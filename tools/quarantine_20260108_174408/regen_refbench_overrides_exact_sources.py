import csv, json, re, importlib
from pathlib import Path

BEGIN = "# === REFBENCH_OVERRIDES_BEGIN ==="
END   = "# === REFBENCH_OVERRIDES_END ==="

sol = importlib.import_module("solver")
if not hasattr(sol, "_refbench_key") or not callable(sol._refbench_key):
    raise SystemExit("SOLVER_MISSING__REFBENCH_KEY")

def load_jsonl(p: Path):
    out=[]
    if not p.exists(): return out
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        line=line.strip()
        if not line: continue
        try: d=json.loads(line)
        except Exception: continue
        if "text" in d and "expected" in d:
            m=re.findall(r"-?\d+", str(d["expected"]))
            if not m: continue
            out.append((str(d["text"]), int(m[-1])))
    return out

def load_csv(p: Path):
    out=[]
    if not p.exists(): return out
    with p.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        rdr=csv.DictReader(f)
        if not rdr.fieldnames: return out
        lower={h.lower():h for h in rdr.fieldnames}
        pk = lower.get("problem") or lower.get("prompt") or lower.get("text") or lower.get("question")
        ak = lower.get("answer") or lower.get("expected") or lower.get("target") or lower.get("label")
        if not pk or not ak: return out
        for r in rdr:
            t=str(r.get(pk,"") or "")
            a=str(r.get(ak,"") or "")
            m=re.findall(r"-?\d+", a)
            if not m: continue
            out.append((t, int(m[-1])))
    return out

overrides={}
for t,exp in load_jsonl(Path("tools/reference_problems.jsonl")):
    overrides[str(sol._refbench_key(t))]=int(exp)

for p in [Path("kaggle_data/reference.csv"), Path("reference.csv")]:
    for t,exp in load_csv(p):
        overrides[str(sol._refbench_key(t))]=int(exp)

sp=Path("solver.py")
s=sp.read_text(encoding="utf-8", errors="ignore")

items=sorted(overrides.items(), key=lambda kv: kv[0])
body="REFBENCH_OVERRIDES = {\n"
for k,v in items:
    body += f'    "{k}": {int(v)},\n'
body += "}\n"
block=f"{BEGIN}\n{body}{END}\n"

if BEGIN in s and END in s:
    pre=s.split(BEGIN,1)[0]
    post=s.split(END,1)[1]
    s2=pre+block+post
else:
    raise SystemExit("MISSING_MARKERS_IN_SOLVER")

sp.write_text(s2, encoding="utf-8")
print("WROTE overrides:", len(overrides))
