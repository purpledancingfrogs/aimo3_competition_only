import json, pathlib
rows = [json.loads(x) for x in pathlib.Path("tools/reference_problems.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
for r in rows:
    t = r["text"].replace("\n"," ")
    print(f'id={r["id"]} expected={r["expected"]} :: {t[:140]}')
