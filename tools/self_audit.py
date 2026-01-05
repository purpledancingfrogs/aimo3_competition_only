import csv, re, sys, pathlib, subprocess, importlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

def sniff_csv(path: pathlib.Path):
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        sample = f.read(4096)
    return csv.Sniffer().sniff(sample, delimiters=",\t;|")

def load_rows(path: pathlib.Path):
    dialect = sniff_csv(path)
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        return list(csv.DictReader(f, dialect=dialect))

def pick_col(cols, want):
    lc = {c.lower(): c for c in cols}
    for w in want:
        for k, v in lc.items():
            if w in k:
                return v
    return None

_int_re = re.compile(r"[-+]?\d+")
def norm_int(s):
    if s is None:
        return None
    s = str(s).strip().replace("\u2212", "-")
    m = _int_re.findall(s)
    return m[-1] if m else None

def load_gold_and_text():
    cand_refs = [
        ROOT/"reference.csv",
        ROOT/"kaggle_data"/"reference.csv",
        ROOT/"kaggle_data"/"reference.csv",
        ROOT/"train.csv",
        ROOT/"kaggle_data"/"train.csv",
    ]
    cand_probs = [
        ROOT/"problems.csv",
        ROOT/"kaggle_data"/"problems.csv",
        ROOT/"input.csv",
        ROOT/"kaggle_data"/"input.csv",
        ROOT/"test.csv",
        ROOT/"kaggle_data"/"test.csv",
    ]
    ref = next((p for p in cand_refs if p.exists()), None)
    prob = next((p for p in cand_probs if p.exists()), None)
    if not ref or not prob:
        print(f"Missing CSVs. ref={ref} prob={prob}", file=sys.stderr)
        sys.exit(2)

    ref_rows = load_rows(ref)
    prob_rows = load_rows(prob)
    if not ref_rows or not prob_rows:
        print("Empty CSV(s).", file=sys.stderr)
        sys.exit(2)

    ref_cols = list(ref_rows[0].keys())
    prob_cols = list(prob_rows[0].keys())

    ref_id  = pick_col(ref_cols,  ["id","problem_id","qid","uid"]) or ref_cols[0]
    ref_ans = pick_col(ref_cols,  ["answer","target","label","y"]) or ref_cols[-1]
    prob_id = pick_col(prob_cols, ["id","problem_id","qid","uid"]) or prob_cols[0]
    prob_tx = pick_col(prob_cols, ["problem","question","text","prompt","statement"]) or prob_cols[-1]

    gold = {r.get(ref_id): r.get(ref_ans) for r in ref_rows}
    text = {r.get(prob_id): r.get(prob_tx) for r in prob_rows}
    common = [k for k in gold.keys() if k in text]
    return ref, prob, common, gold, text

def load_solver_callable():
    sys.path.insert(0, str(ROOT))
    try:
        mod = importlib.import_module("solver")
        if hasattr(mod, "Solver"):
            s = mod.Solver()
            if hasattr(s, "solve") and callable(getattr(s, "solve")):
                return lambda t: s.solve(t)
        if hasattr(mod, "solve") and callable(getattr(mod, "solve")):
            return lambda t: mod.solve(t)
    except Exception:
        pass

    solver_path = ROOT / "solver.py"
    if not solver_path.exists():
        raise RuntimeError("solver.py not found at repo root")

    def run_as_script(t):
        p = subprocess.run(
            [sys.executable, str(solver_path)],
            input=t,
            text=True,
            capture_output=True,
        )
        out = (p.stdout or "").strip()
        if out:
            return out
        err = (p.stderr or "").strip()
        return f"__NO_STDOUT__:{p.returncode}:{err[:160]}"
    return run_as_script

def main():
    ref, prob, ids, gold, text = load_gold_and_text()
    solve = load_solver_callable()

    out_md = ROOT/"audit"/"reports"/"misses_summary.md"
    out_jsonl = ROOT/"audit"/"reports"/"misses.jsonl"

    total = 0
    correct = 0
    misses = []

    for k in ids:
        total += 1
        q = text.get(k, "")
        g = norm_int(gold.get(k))
        try:
            p_raw = solve(q)
        except Exception as e:
            p_raw = f"__EXC__:{type(e).__name__}:{str(e)[:120]}"
        p = norm_int(p_raw)
        if p is not None and g is not None and p == g:
            correct += 1
        else:
            snippet = " ".join(str(q).split())[:180]
            misses.append((k, g, p, str(p_raw)[:120], snippet))

    acc = (correct / total) if total else 0.0

    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("w", encoding="utf-8") as f:
        for k,g,p,praw,sn in misses:
            f.write(f'{{"id":"{k}","gold":"{g}","pred":"{p}","pred_raw":"{praw}","snippet":"{sn}"}}\\n')

    with out_md.open("w", encoding="utf-8") as f:
        f.write(f"ref={ref.name} prob={prob.name}\\n")
        f.write(f"TOTAL={total} CORRECT={correct} ACC={acc:.4f} MISSES={len(misses)}\\n\\n")
        f.write("Top 50 misses:\\n")
        for i,(k,g,p,praw,sn) in enumerate(misses[:50], 1):
            f.write(f"{i:02d}. id={k} gold={g} pred={p} pred_raw={praw} :: {sn}\\n")

    print(str(out_md))
    print(f"TOTAL={total} CORRECT={correct} ACC={acc:.4f} MISSES={len(misses)}")

if __name__ == "__main__":
    main()
