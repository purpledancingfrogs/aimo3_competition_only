import csv
import subprocess
import sys

INPUT = "problems.csv"
OUTPUT = "submission.csv"

with open(INPUT, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "answer"])

    for r in rows:
        p = subprocess.run(
            ["python", "solver.py", r["problem"]],
            capture_output=True,
            text=True
        )
        ans = p.stdout.strip()
        if ans == "":
            ans = "0"
        writer.writerow([r["id"], ans])

print("DONE:", len(rows), "problems")
