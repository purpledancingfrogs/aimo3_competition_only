import csv, json, re
from pathlib import Path

def find_candidate_files(root: Path):
    include = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in [".csv", ".jsonl"]:
            continue
        s = p.as_posix().lower()
        if any(k in s for k in ["competition", "competitions", "evaluation", "eval", "reference", "bench", "dataset", "data"]):
            include.append(p)
    return include

PROMPT_KEYS = ["problem", "question", "text", "prompt", "input"]
ANSWER_KEYS = ["answer", "expected", "target", "label", "output"]

_int_re = re.compile(r"-?\d+")

def extract_int(x):
    if x is None:
        return None
    if isinstance(x, int):
        return int(x)
    if isinstance(x, float) and x.is_integer():
        return int(x)
    s = str(x).strip()
    m = _int_re.findall(s)
    if not m:
        return None
    return int(m[-1])

def pick_key(d, keys):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return k
    low = {str(k).lower(): k for k in d.keys()}
    for k in keys:
        if k in low:
            kk = low[k]
            if d[kk] not in (None, ""):
                return kk
    return None

def load_rows(path: Path):
    rows = []
    if path.suffix.lower() == ".jsonl":
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            pk = pick_key(d, PROMPT_KEYS)
            ak = pick_key(d, ANSWER_KEYS)
            if not pk or not ak:
                continue
            exp = extract_int(d.get(ak))
            if exp is None:
                continue
            rows.append((str(d.get(pk)), exp))
    else:
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
            try:
                rdr = csv.DictReader(f)
            except Exception:
                return rows
            if not rdr.fieldnames:
                return rows
            for d in rdr:
                pk = pick_key(d, PROMPT_KEYS)
                ak = pick_key(d, ANSWER_KEYS)
                if not pk or not ak:
                    continue
                exp = extract_int(d.get(ak))
                if exp is None:
                    continue
                rows.append((str(d.get(pk)), exp))
    return rows

def main():
    import solver
    root = Path(".")
    files = find_candidate_files(root)

    out_dir = Path("tools")
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    failures = []

    total = 0
    ok = 0

    for fp in sorted(files):
        rows = load_rows(fp)
        if not rows:
            continue
        rows = rows[:500]
        f_total = 0
        f_ok = 0
        for (txt, exp) in rows:
            total += 1
            f_total += 1
            try:
                got = solver.solve(txt)
                got_i = extract_int(got)
            except Exception as e:
                got_i = None
                got = f"EXC:{type(e).__name__}:{e}"
            if got_i == exp:
                ok += 1
                f_ok += 1
                status = "OK"
            else:
                status = "WRONG"
                if len(failures) < 300:
                    failures.append({
                        "file": fp.as_posix(),
                        "expected": exp,
                        "got": got_i,
                        "got_raw": str(got)[:200],
                        "text_head": txt[:400],
                    })
            results.append({
                "file": fp.as_posix(),
                "status": status,
                "expected": exp,
                "got": got_i,
            })

        acc = (f_ok / f_total) if f_total else 0.0
        print(f"FILE {fp.as_posix()}  N={f_total}  OK={f_ok}  ACC={acc:.3f}")

    (out_dir / "surrogate_summary.txt").write_text(
        f"TOTAL={total}\nOK={ok}\nACC={(ok/total if total else 0):.6f}\nFILES_SCANNED={len(files)}\n",
        encoding="utf-8"
    )
    with (out_dir / "surrogate_failures.jsonl").open("w", encoding="utf-8") as f:
        for x in failures:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")

    print("TOTAL", total, "OK", ok, "ACC", (ok/total if total else 0))
    print("WROTE tools/surrogate_summary.txt")
    print("WROTE tools/surrogate_failures.jsonl")

if __name__ == "__main__":
    main()
