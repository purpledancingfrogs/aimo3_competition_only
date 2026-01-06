import os, csv, json, time, statistics, glob

def pick_col(fieldnames, candidates):
    fset = {f.lower(): f for f in fieldnames}
    for c in candidates:
        if c.lower() in fset:
            return fset[c.lower()]
    return None

def get_solver_callable(mod):
    if hasattr(mod, "Solver"):
        inst = mod.Solver()
        if hasattr(inst, "solve"):
            return inst.solve
    if hasattr(mod, "solve") and callable(mod.solve):
        return mod.solve
    raise RuntimeError("No solver callable found (expected Solver().solve or solve())")

def iter_csv_rows(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        rows = list(r)
        return r.fieldnames or [], rows

def main():
    import solver
    solve_fn = get_solver_callable(solver)
    out_dir = os.path.join("tools","_outputs")
    os.makedirs(out_dir, exist_ok=True)

    candidates = []
    candidates += glob.glob(os.path.join("kaggle_data","*.csv"))
    candidates += glob.glob(os.path.join("kaggle_data","**","*.csv"), recursive=True)
    candidates = sorted(set(candidates))

    summ_lines = []
    summ_lines.append("DATASET_PROBE")
    summ_lines.append(f"found_csv={len(candidates)}")

    sample_path = os.path.join(out_dir, "probe_samples.jsonl")
    with open(sample_path, "w", encoding="utf-8") as sf:
        for path in candidates:
            fieldnames, rows = iter_csv_rows(path)
            if not fieldnames or not rows:
                summ_lines.append(f"- {path}: EMPTY")
                continue

            pcol = pick_col(fieldnames, ["prompt","problem","question","input","text"])
            acol = pick_col(fieldnames, ["answer","target","label","output"])
            if pcol is None:
                summ_lines.append(f"- {path}: NO_PROMPT_COL fields={fieldnames}")
                continue

            n = len(rows)
            times = []
            ok = 0
            has_ans = (acol is not None)
            for i, row in enumerate(rows):
                prompt = (row.get(pcol) or "")
                exp = (row.get(acol) or "").strip() if has_ans else None
                t0 = time.perf_counter()
                try:
                    pred = str(solve_fn(prompt)).strip()
                    err = None
                except Exception as e:
                    pred = "0"
                    err = f"{type(e).__name__}:{e}"
                dt = time.perf_counter() - t0
                times.append(dt)

                if has_ans and exp is not None:
                    ok += int(pred == exp)

                if i < 50:
                    sf.write(json.dumps({
                        "file": path,
                        "row": i,
                        "len": len(prompt),
                        "head": prompt[:120],
                        "tail": prompt[-120:],
                        "pred": pred,
                        "exp": exp,
                        "err": err,
                        "sec": round(dt, 6),
                    }, ensure_ascii=False) + "\n")

            p50 = statistics.median(times) if times else 0.0
            p90 = sorted(times)[int(0.9*len(times))-1] if len(times) >= 2 else (times[0] if times else 0.0)
            mx = max(times) if times else 0.0
            if has_ans:
                summ_lines.append(f"- {path}: rows={n} ok={ok} acc={(ok/n if n else 0.0):.6f} t_med={p50:.4f}s t_p90={p90:.4f}s t_max={mx:.4f}s")
            else:
                summ_lines.append(f"- {path}: rows={n} (no answer col) t_med={p50:.4f}s t_p90={p90:.4f}s t_max={mx:.4f}s")

    summ_path = os.path.join(out_dir, "probe_summary.txt")
    with open(summ_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summ_lines) + "\n")
    print(open(summ_path, "r", encoding="utf-8").read().strip())

if __name__ == "__main__":
    main()
