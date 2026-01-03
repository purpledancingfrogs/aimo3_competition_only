import csv
import sys
from solver import solve

def main(inp, out):
    with open(inp, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "prediction"])
        w.writeheader()
        for r in rows:
            w.writerow({"id": r["id"], "prediction": solve(r["problem"])})

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python run.py input.csv output.csv")
    main(sys.argv[1], sys.argv[2])
