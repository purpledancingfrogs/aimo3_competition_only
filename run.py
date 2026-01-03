import csv
import sys
from solver import solve

def main(inp, outp):
    with open(inp, newline='', encoding='utf-8') as f, open(outp, 'w', newline='', encoding='utf-8') as g:
        reader = csv.DictReader(f)
        fieldnames = ["id", "prediction"]
        writer = csv.DictWriter(g, fieldnames=fieldnames)
        writer.writeheader()

        auto_id = 0
        for row in reader:
            prob = row.get("problem") or row.get("question") or row.get("input")
            if prob is None:
                continue
            rid = row.get("id")
            if rid is None:
                rid = auto_id
                auto_id += 1
            writer.writerow({"id": rid, "prediction": solve(prob)})

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
