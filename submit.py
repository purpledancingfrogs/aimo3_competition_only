import json
import pandas as pd
from meta_solver import solve

INPUT = "test.json"
OUTPUT = "submission.parquet"

with open(INPUT, "r") as f:
    data = json.load(f)

rows = []
for item in data:
    pid = item["id"]
    problem = item["problem"]
    ans = solve(problem)
    if ans is None:
        ans = ""
    rows.append({"id": pid, "answer": str(ans)})

df = pd.DataFrame(rows)
df.to_parquet(OUTPUT, index=False)
print("submission.parquet written")
