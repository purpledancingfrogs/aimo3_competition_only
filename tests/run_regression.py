import csv, json, sys, time
from pathlib import Path

def _load_jsonl(p: Path):
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        yield json.loads(line)

def main():
    jsonl = Path("tests/regression.jsonl")
    if not jsonl.exists():
        raise SystemExit("MISSING:tests/regression.jsonl (run STEP 1 extractor)")
    import solver
    s = solver.Solver() if hasattr(solver, "Solver") else None
    if s is None or not hasattr(s, "solve"):
        raise SystemExit("MISSING_ENTRYPOINT: solver.Solver().solve(text)")
    out_csv = Path("tests/out_regression.csv")
    fail_csv = Path("tests/failures.csv")

    rows = []
    fails = []
    t0 = time.time()
    for rec in _load_jsonl(jsonl):
        pid = str(rec.get("id",""))
        text = str(rec.get("text",""))
        expected = rec.get("expected", None)
        try:
            got = s.solve(text)
        except Exception as e:
            got = "EXC"
            fails.append([pid, "EXCEPTION", repr(e)])
        rows.append([pid, expected if expected is not None else "", str(got)])

        if expected is not None and str(got).strip() != str(expected).strip():
            fails.append([pid, "MISMATCH", f"expected={expected} got={got}"])

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id","expected","got"])
        w.writerows(rows)

    with fail_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id","kind","detail"])
        w.writerows(fails)

    dt = time.time() - t0
    print(f"RAN={len(rows)} FAILS={len(fails)} SECS={dt:.3f}")
    if fails:
        raise SystemExit("REGRESSION_FAIL")

if __name__ == "__main__":
    main()
