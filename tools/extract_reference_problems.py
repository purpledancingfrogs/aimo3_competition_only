import re, json, pathlib

src = pathlib.Path("tools/reference_dump.txt").read_text(encoding="utf-8", errors="ignore")

# Headings in the PDF dump are standalone lines like: "Problem 1"
head_pat = re.compile(r"(?m)^\s*Problem\s+(\d{1,2})\s*$")
heads = [(m.start(), int(m.group(1))) for m in head_pat.finditer(src)]
heads.sort()

rows = []
for i, (pos, pid) in enumerate(heads):
    end = heads[i+1][0] if i+1 < len(heads) else len(src)
    block = src[pos:end]

    # Cut at Answer: (keep only the problem statement section)
    m_ans_line = re.search(r"(?m)^\s*Answer:\s*([-]?\d+)\s*$", block)
    expected = int(m_ans_line.group(1)) if m_ans_line else None
    cut = m_ans_line.start() if m_ans_line else len(block)
    prob_text = block[:cut].strip()

    # Light cleanup
    prob_text = re.sub(r"(?m)^===== PAGE.*?=====\s*$", "", prob_text).strip()
    rows.append({"id": pid, "expected": expected, "text": prob_text})

# De-dup by id (keep first)
dedup = {}
for r in rows:
    dedup.setdefault(r["id"], r)

out = pathlib.Path("tools/reference_problems.jsonl")
with out.open("w", encoding="utf-8") as f:
    for k in sorted(dedup.keys()):
        f.write(json.dumps(dedup[k], ensure_ascii=False) + "\n")

print(f"HEADS_FOUND={len(heads)}")
print(f"PROBLEMS_WRITTEN={len(dedup)} -> {out}")
if dedup:
    print("IDS=", sorted(dedup.keys()))
    missing = [k for k,v in dedup.items() if v["expected"] is None]
    print("MISSING_EXPECTED_IDS=", missing)
