import csv, subprocess, sys, json, hashlib
from pathlib import Path

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()

def find_one(name):
    for p in Path(".").rglob(name):
        return p
    return None

train = find_one("train.csv")
audit = Path("audit"); audit.mkdir(exist_ok=True)

if not train:
    (audit/"eval_summary.json").write_text(json.dumps({"train_path":None,"note":"train.csv not found; cannot compute accuracy"},indent=2),encoding="utf-8")
    print("NO train.csv FOUND")
    raise SystemExit(0)

rows=[]
with train.open(newline="",encoding="utf-8") as f:
    dr=csv.DictReader(f)
    for row in dr:
        rows.append((row.get("id","").strip(), row.get("problem",""), str(row.get("answer","")).strip()))

out_path = Path("eval_report.csv")
misses=[]
ok=0

with out_path.open("w",newline="",encoding="utf-8") as g:
    w=csv.DictWriter(g,fieldnames=["id","gold","pred","ok"])
    w.writeheader()
    for pid,prob,gold in rows:
        try:
            pred=subprocess.check_output([sys.executable,"solver.py"],input=prob.encode("utf-8"),stderr=subprocess.DEVNULL).decode("utf-8").strip()
        except Exception:
            pred=""
        if pred=="":
            pred="0"
        good=int(pred==gold)
        ok+=good
        w.writerow({"id":pid,"gold":gold,"pred":pred,"ok":good})
        if not good and len(misses)<30:
            sn=prob.replace("\n"," ").strip()
            if len(sn)>220: sn=sn[:220]+"…"
            misses.append({"id":pid,"gold":gold,"pred":pred,"problem_snippet":sn})

acc=(ok/len(rows)) if rows else 0.0
summary={
  "train_path": str(train),
  "rows": len(rows),
  "correct": ok,
  "accuracy": acc,
  "first_misses": misses,
  "files": {
    "train.csv": {"sha256": sha256_file(train), "bytes": train.stat().st_size},
    "eval_report.csv": {"sha256": sha256_file(out_path), "bytes": out_path.stat().st_size},
  }
}
(audit/"eval_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(f"train={train} rows={len(rows)} correct={ok} accuracy={acc}")
