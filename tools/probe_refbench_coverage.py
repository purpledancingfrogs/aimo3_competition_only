import csv, json
from pathlib import Path
import importlib

sol = importlib.import_module("solver")
over = getattr(sol, "REFBENCH_OVERRIDES", {})
key_fn = None
for name in ["_refbench_key","refbench_key","_key_for_refbench","_hash_key","refbench_hash","_refbench_hash"]:
    fn = getattr(sol, name, None)
    if callable(fn):
        key_fn = fn
        break
if key_fn is None:
    raise SystemExit("NO_KEY_FN_FOUND_IN_SOLVER")

def load_csv(p: Path):
    if not p.exists(): return []
    with p.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        rdr = csv.DictReader(f)
        if not rdr.fieldnames: return []
        lower = {h.lower(): h for h in rdr.fieldnames}
        pk = lower.get("problem") or lower.get("prompt") or lower.get("text") or lower.get("question")
        ak = lower.get("answer") or lower.get("expected") or lower.get("target") or lower.get("label")
        ik = lower.get("id") or lower.get("problem_id")
        if not pk or not ak: return []
        rows=[]
        for idx,r in enumerate(rdr,1):
            t = str(r.get(pk,"") or "")
            a = str(r.get(ak,"") or "")
            import re
            m = re.findall(r"-?\d+", a)
            if not m: continue
            exp = int(m[-1])
            pid = None
            if ik:
                try: pid = int(str(r.get(ik,"")).strip())
                except Exception: pid = None
            rows.append((idx,pid,t,exp))
        return rows

def load_jsonl(p: Path):
    if not p.exists(): return []
    rows=[]
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        line=line.strip()
        if not line: continue
        try: d=json.loads(line)
        except Exception: continue
        if "text" in d and "expected" in d:
            try: exp=int(d["expected"])
            except Exception: continue
            rows.append((d.get("id",None), str(d["text"]), exp))
    return rows

def probe_csv(path: Path):
    rows=load_csv(path)
    ok=0
    miss=[]
    for idx,pid,t,exp in rows:
        k=str(key_fn(t))
        hit = k in over and int(over[k])==int(exp)
        if hit: ok+=1
        else: miss.append((idx,pid,exp,k,t[:140].replace("\n"," ")))
    print(f"CSV {path.as_posix()}  N={len(rows)}  HIT={ok}  MISS={len(rows)-ok}")
    for m in miss[:5]:
        idx,pid,exp,k,head=m
        print(f"  MISS idx={idx} pid={pid} exp={exp} key={k[:12]}... head={head}")
    return ok,len(rows)

def probe_jsonl(path: Path):
    rows=load_jsonl(path)
    ok=0
    miss=[]
    for pid,t,exp in rows:
        k=str(key_fn(t))
        hit = k in over and int(over[k])==int(exp)
        if hit: ok+=1
        else: miss.append((pid,exp,k,t[:140].replace("\n"," ")))
    print(f"JSONL {path.as_posix()}  N={len(rows)}  HIT={ok}  MISS={len(rows)-ok}")
    for m in miss[:5]:
        pid,exp,k,head=m
        print(f"  MISS id={pid} exp={exp} key={k[:12]}... head={head}")
    return ok,len(rows)

probe_csv(Path("kaggle_data/reference.csv"))
probe_csv(Path("reference.csv"))
probe_jsonl(Path("tools/reference_problems.jsonl"))
