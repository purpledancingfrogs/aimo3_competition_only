from __future__ import annotations
import csv, json, re, sys, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "audit" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def _lower_set(headers):
    return {h.lower(): h for h in headers}

def pick_col(headers, candidates):
    m = _lower_set(headers)
    for c in candidates:
        if c.lower() in m:
            return m[c.lower()]
    return None

def read_rows(p: Path):
    with p.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        rows = list(r)
        return r.fieldnames or [], rows

def find_first_existing(paths):
    for p in paths:
        if p.exists():
            return p
    return None

def normalize_answer(s: str):
    s = (s or "").strip()
    if s == "":
        return ""
    # prefer last integer if present
    m = re.findall(r"[-+]?\d+", s)
    if m:
        try:
            return str(int(m[-1]))
        except Exception:
            pass
    return s

def solve_via_import(text: str):
    try:
        import importlib
        sol = importlib.import_module("solver")
        if hasattr(sol, "Solver") and hasattr(sol.Solver, "solve"):
            return str(sol.Solver().solve(text)).strip()
        if hasattr(sol, "solve"):
            return str(sol.solve(text)).strip()
    except Exception:
        return None
    return None

def solve_via_subprocess(text: str):
    cmd = [sys.executable, str(ROOT / "solver.py")]
    p = subprocess.run(cmd, input=text, text=True, capture_output=True, timeout=25)
    out = (p.stdout or "").strip()
    if out == "":
        out = (p.stderr or "").strip()
    # take last non-empty line
    lines = [ln.strip() for ln in out.splitlines() if ln.strip() != ""]
    return lines[-1] if lines else ""

def solve_one(text: str):
    ans = solve_via_import(text)
    if ans is not None and ans != "":
        return ans
    return solve_via_subprocess(text)

def main():
    prob_path = find_first_existing([
        ROOT / "problems.csv",
        ROOT / "kaggle_data" / "problems.csv",
        ROOT / "kaggle_data" / "train.csv",
        ROOT / "kaggle_data" / "test.csv",
        ROOT / "test.csv",
    ])
    ref_path = find_first_existing([
        ROOT / "reference.csv",
        ROOT / "kaggle_data" / "reference.csv",
    ])

    if prob_path is None:
        raise SystemExit("No problems/test CSV found (looked for problems.csv, kaggle_data/{problems,train,test}.csv, test.csv).")
    if ref_path is None:
        print("WARNING: reference.csv not found; will run solver but cannot score.", file=sys.stderr)

    p_headers, p_rows = read_rows(prob_path)
    if not p_rows:
        raise SystemExit(f"{prob_path} has 0 rows.")

    # schema detection
    p_id = pick_col(p_headers, ["id", "problem_id", "uid"])
    p_text = pick_col(p_headers, ["problem", "question", "text", "prompt", "statement"])
    p_gold_inline = pick_col(p_headers, ["answer", "output", "target", "label", "gold"])

    if p_text is None:
        raise SystemExit(f"Cannot find problem text column in {prob_path}. Headers={p_headers}")

    gold_map = {}
    r_id = r_gold = None
    if ref_path is not None:
        r_headers, r_rows = read_rows(ref_path)
        r_id = pick_col(r_headers, ["id", "problem_id", "uid"])
        r_gold = pick_col(r_headers, ["answer", "output", "target", "label", "gold"])
        if r_id and r_gold:
            for row in r_rows:
                k = (row.get(r_id) or "").strip()
                if k != "":
                    gold_map[k] = row.get(r_gold, "")
        else:
            print(f"WARNING: reference.csv schema not recognized. Headers={r_headers}", file=sys.stderr)

    total = correct = 0
    misses = []

    for row in p_rows:
        pid = (row.get(p_id, "") if p_id else str(total)).strip()
        text = row.get(p_text, "") or ""
        gold = ""
        if pid in gold_map:
            gold = gold_map[pid]
        elif p_gold_inline:
            gold = row.get(p_gold_inline, "")
        pred_raw = solve_one(text)
        pred = normalize_answer(pred_raw)
        gold_n = normalize_answer(gold)

        if gold_n != "":
            total += 1
            ok = (pred == gold_n)
            if ok:
                correct += 1
            else:
                snippet = " ".join(text.split())[:220]
                misses.append({
                    "id": pid,
                    "gold": gold_n,
                    "pred": pred,
                    "pred_raw": (pred_raw or "")[:4000],
                    "snippet": snippet,
                })

    out_jsonl = REPORT_DIR / "misses.jsonl"
    out_md = REPORT_DIR / "misses_summary.md"

    with out_jsonl.open("w", encoding="utf-8") as f:
        for m in misses:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    acc = (correct / total) if total else 0.0
    with out_md.open("w", encoding="utf-8") as f:
        f.write(f"generated_at={datetime.utcnow().isoformat()}Z\n")
        f.write(f"prob_path={prob_path}\nref_path={ref_path}\n")
        f.write(f"TOTAL={total} CORRECT={correct} ACC={acc:.4f} MISSES={len(misses)}\n\n")
        f.write("Top 50 misses:\n")
        for i, m in enumerate(misses[:50], 1):
            f.write(f"{i:02d}. id={m['id']} gold={m['gold']} pred={m['pred']} :: {m['snippet']}\n")

    print(out_md)
    print(f"TOTAL={total} CORRECT={correct} ACC={acc:.4f} MISSES={len(misses)}")
    if total == 0:
        print("NOTE: No gold labels found to score against (reference.csv missing/unrecognized and no inline answer column).", file=sys.stderr)

if __name__ == "__main__":
    main()