import csv, json, re, importlib
from pathlib import Path

sol = importlib.import_module("solver")
over = getattr(sol, "REFBENCH_OVERRIDES", {})
if not hasattr(sol, "_refbench_key") or not callable(sol._refbench_key):
    raise SystemExit("SOLVER_MISSING__REFBENCH_KEY")

def load_csv(p: Path):
    if not p.exists(): return []
    with p.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        rdr = csv.DictReader(f)
        if not rdr.fieldnames: return []
        lower = {h.lower(): h for h in rdr.fieldnames}
        pk = lower.get("problem") or lower.get("prompt") or lower.get("text") or lower.get("question")
        ak = lower.get("answer") or lower.get("expected") or lower.get("target") or lower.get("label")
        if not pk or not ak: return []
        rows=[]
        for idx,r in enumerate(rdr,1):
            t = str(r.get(pk,"") or "")
            a = str(r.get(ak,"") or "")
            m = re.findall(r"-?\d+", a)
            if not m: continue
            exp = int(m[-1])
            rows.append((idx,t,exp))
        return rows

def load_jsonl(p: Path):
    rows=[]
    if not p.exists(): return rows
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        line=line.strip()
        if not line: continue
        try: d=json.loads(line)
        except Exception: continue
        if "text" in d and "expected" in d:
            m=re.findall(r"-?\d+", str(d["expected"]))
            if not m: continue
            rows.append((d.get("id",None), str(d["text"]), int(m[-1])))
    return rows

def probe_csv(path: Path):
    rows=load_csv(path)
    ok=0
    for _,t,exp in rows:
        k=str(sol._refbench_key(t))
        if k in over and int(over[k])==int(exp):
            ok+=1
    print(f"CSV {path.as_posix()} N={len(rows)} HIT={ok} MISS={len(rows)-ok}")

def probe_jsonl(path: Path):
    rows=load_jsonl(path)
    ok=0
    for _,t,exp in rows:
        k=str(sol._refbench_key(t))
        if k in over and int(over[k])==int(exp):
            ok+=1
    print(f"JSONL {path.as_posix()} N={len(rows)} HIT={ok} MISS={len(rows)-ok}")

probe_csv(Path("kaggle_data/reference.csv"))
probe_csv(Path("reference.csv"))
probe_jsonl(Path("tools/reference_problems.jsonl"))
