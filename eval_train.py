import csv, glob, hashlib, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(".").resolve()
AUDIT = ROOT / "audit"
AUDIT.mkdir(exist_ok=True)

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def find_trainlike_csv():
    candidates = []
    for p in glob.glob("**/*.csv", recursive=True):
        pn = Path(p)
        if pn.name.lower() in {"submission.csv","audit_test.csv","sample_submission.csv","test.csv"}:
            continue
        if "audit" in pn.parts:
            continue
        try:
            with pn.open(newline="", encoding="utf-8") as f:
                r = csv.reader(f)
                header = next(r, None)
            if not header:
                continue
            cols = set([c.strip() for c in header])
            if {"id","problem","answer"}.issubset(cols):
                candidates.append(str(pn))
        except Exception:
            continue
    return candidates[0] if candidates else None

def run_eval(train_path: str):
    out_csv = ROOT / "eval_report.csv"
    out_json = AUDIT / "eval_summary.json"
    log_path = AUDIT / "eval_run.log"

    t0 = time.time()
    rows = []
    with open(train_path, newline="", encoding="utf-8") as f:
        dr = csv.DictReader(f)
        for row in dr:
            rows.append({
                "id": (row.get("id","") or "").strip(),
                "problem": row.get("problem","") or "",
                "answer": (row.get("answer","") or "").strip()
            })

    misses = []
    ok = 0
    with out_csv.open("w", newline="", encoding="utf-8") as g:
        w = csv.DictWriter(g, fieldnames=["id","gold","pred","ok"])
        w.writeheader()
        for row in rows:
            pid = row["id"]
            prob = row["problem"]
            gold = row["answer"]
            try:
                pred = subprocess.check_output(
                    [sys.executable, "solver.py"],
                    input=prob.encode("utf-8"),
                    stderr=subprocess.DEVNULL
                ).decode("utf-8").strip()
            except Exception:
                pred = ""
            if pred == "":
                pred = "0"
            good = int(pred == gold)
            ok += good
            w.writerow({"id": pid, "gold": gold, "pred": pred, "ok": good})
            if not good and len(misses) < 25:
                snippet = prob.replace("\n"," ").strip()
                if len(snippet) > 200:
                    snippet = snippet[:200] + "…"
                misses.append({"id": pid, "gold": gold, "pred": pred, "problem_snippet": snippet})

    acc = (ok / len(rows)) if rows else 0.0
    summary = {
        "train_path": train_path,
        "rows": len(rows),
        "correct": ok,
        "accuracy": acc,
        "first_misses": misses,
        "seconds": round(time.time() - t0, 3)
    }
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log_path.write_text(f"train_path={train_path}\nrows={len(rows)}\ncorrect={ok}\naccuracy={acc}\n", encoding="utf-8")
    return summary

train = find_trainlike_csv()
if not train:
    (ROOT / "eval_report.csv").write_text("id,gold,pred,ok\n", encoding="utf-8")
    (AUDIT / "eval_summary.json").write_text(json.dumps({"train_path": None, "rows": 0, "correct": 0, "accuracy": None, "note": "NO_TRAINLIKE_CSV_FOUND"}, indent=2), encoding="utf-8")
    print("NO_TRAINLIKE_CSV_FOUND")
    sys.exit(0)

s = run_eval(train)
print(f"train={train}")
print(f"rows={s['rows']} correct={s['correct']} accuracy={s['accuracy']}")
