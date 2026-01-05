import argparse, csv, subprocess, sys
from pathlib import Path

def solve_one(text: str) -> str:
    try:
        out = subprocess.check_output(
            [sys.executable, "solver.py"],
            input=(text or "").encode("utf-8"),
            stderr=subprocess.DEVNULL,
        ).decode("utf-8", errors="replace").strip()
        return out if out != "" else "0"
    except Exception:
        return "0"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="CSV with columns: id, problem")
    ap.add_argument("--output", required=True, help="CSV to write with columns: id, answer")
    ap.add_argument("--deterministic", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    inp = Path(args.input)
    if not inp.exists():
        raise SystemExit(f"INPUT NOT FOUND: {inp}")

    with inp.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as g:
        w = csv.writer(g)
        w.writerow(["id", "answer"])
        for row in rows:
            pid = row.get("id", "")
            prob = row.get("problem", "")
            ans = solve_one(prob)
            w.writerow([pid, ans])

    if args.validate:
        # Basic schema check
        with out_path.open("r", newline="", encoding="utf-8") as f:
            out_rows = list(csv.reader(f))
        if out_rows[0] != ["id", "answer"]:
            raise SystemExit(f"BAD HEADER: {out_rows[0]}")
        if len(out_rows) - 1 != len(rows):
            raise SystemExit(f"ROWCOUNT MISMATCH: in={len(rows)} out={len(out_rows)-1}")

    print(f"DONE: {len(rows)} problems")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
