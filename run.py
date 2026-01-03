import csv
import sys
from solver import solve

def main(inp, outp):
    with open(inp, newline="", encoding="utf-8") as f, open(outp, "w", newline="", encoding="utf-8") as g:
        reader = csv.DictReader(f)
        # Accept either "id" or positional index if id is missing
        fieldnames = ["id", "prediction"]
        writer = csv.DictWriter(g, fieldnames=fieldnames)
        writer.writeheader()
        for i, r in enumerate(reader):
            rid = r.get("id", i)
            prob = r.get("problem") or r.get("question") or ""
            writer.writerow({"id": rid, "prediction": solve(prob)})

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python run.py <input.csv> <output.csv>")
    main(sys.argv[1], sys.argv[2])
