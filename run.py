import csv
from solver import solve

with open("test.csv", newline="") as f:
    rows = list(csv.DictReader(f))

with open("submission.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=["id","prediction"])
    w.writeheader()
    for r in rows:
        w.writerow({"id":r["id"],"prediction":solve(r["problem"])})
