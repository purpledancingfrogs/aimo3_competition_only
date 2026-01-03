import csv
from solver import solve

with open("test.csv", newline="") as f:
    rows = list(csv.DictReader(f))

with open("output.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "prediction"])
    writer.writeheader()
    for r in rows:
        writer.writerow({
            "id": r["id"],
            "prediction": solve(r["problem"])
        })
