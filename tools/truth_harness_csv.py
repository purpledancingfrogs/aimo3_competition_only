import argparse, csv, json

def pick_col(fieldnames, candidates):
    fset = {f.lower(): f for f in fieldnames}
    for c in candidates:
        if c.lower() in fset:
            return fset[c.lower()]
    return None

def load_rows(csv_path):
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        rows = list(r)
        return r.fieldnames, rows

def get_solver_callable(mod):
    if hasattr(mod, "Solver"):
        inst = mod.Solver()
        if hasattr(inst, "solve"):
            return inst.solve
    if hasattr(mod, "solve") and callable(mod.solve):
        return mod.solve
    raise RuntimeError("No solver callable found (expected Solver().solve or solve())")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out_prefix", required=True)
    args = ap.parse_args()

    import solver
    if not hasattr(solver, "_refbench_key") or not callable(solver._refbench_key):
        raise SystemExit("MISSING: solver._refbench_key(text)")

    solve_fn = get_solver_callable(solver)
    fieldnames, rows = load_rows(args.csv)
    if not fieldnames:
        raise SystemExit("EMPTY_CSV: " + args.csv)

    prompt_col = pick_col(fieldnames, ["prompt","problem","question","input","text"])
    ans_col    = pick_col(fieldnames, ["answer","target","label","output"])
    if prompt_col is None or ans_col is None:
        raise SystemExit("COLS_NOT_FOUND: fields=" + str(fieldnames))

    total = 0
    ok = 0
    failures = []

    for i, row in enumerate(rows):
        prompt = (row.get(prompt_col) or "")
        exp = (row.get(ans_col) or "").strip()
        total += 1
        try:
            pred = str(solve_fn(prompt)).strip()
            err = None
        except Exception as e:
            pred = "0"
            err = type(e).__name__ + ":" + str(e)

        k = solver._refbench_key(prompt)
        is_ok = (pred == exp)
        ok += 1 if is_ok else 0

        if not is_ok:
            failures.append({
                "row": i,
                "len": len(prompt),
                "key": k,
                "prompt_head": prompt[:80],
                "prompt_tail": prompt[-80:],
                "pred": pred,
                "exp": exp,
                "err": err,
            })

    summ_path = args.out_prefix + "_summary.txt"
    fail_path = args.out_prefix + "_failures.jsonl"

    with open(summ_path, "w", encoding="utf-8") as f:
        f.write("csv=" + args.csv + "\n")
        f.write("rows=" + str(total) + "\n")
        f.write("ok=" + str(ok) + "\n")
        f.write("acc=" + ("%.6f" % (ok/total if total else 0.0)) + "\n")
        f.write("failures=" + str(len(failures)) + "\n")

    with open(fail_path, "w", encoding="utf-8") as f:
        for rec in failures:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with open(summ_path, "r", encoding="utf-8") as f:
        print(f.read().strip())

if __name__ == "__main__":
    main()
