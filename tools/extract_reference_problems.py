import re, json, pathlib

src = pathlib.Path("tools/reference_dump.txt").read_text(encoding="utf-8", errors="ignore")

# Primary: "Problem 1", "Problem 12", or "1.", "12)"
pat = re.compile(r"(?m)^(?:\s*Problem\s*)?(\d{1,3})\s*[\.\)\:]\s+")
hits = [(m.start(), int(m.group(1))) for m in pat.finditer(src)]

# De-dup consecutive identical IDs while keeping first occurrence
dedup = []
seen_pos = set()
last_id = None
for pos, pid in hits:
    if (pos in seen_pos): 
        continue
    if pid == last_id:
        continue
    dedup.append((pos, pid))
    seen_pos.add(pos)
    last_id = pid

problems = []
if len(dedup) >= 10:
    for i, (pos, pid) in enumerate(dedup):
        end = dedup[i+1][0] if i+1 < len(dedup) else len(src)
        chunk = src[pos:end].strip()
        # keep chunk if it looks non-trivial
        if len(chunk) >= 80:
            problems.append({"id": pid, "text": chunk})
else:
    # Fallback: split by large gaps and keep substantial blocks
    blocks = re.split(r"\n{3,}", src)
    pid = 1
    for b in blocks:
        b = b.strip()
        if len(b) >= 200:
            problems.append({"id": pid, "text": b})
            pid += 1

out = pathlib.Path("tools/reference_problems.jsonl")
with out.open("w", encoding="utf-8") as f:
    for p in problems:
        f.write(json.dumps(p, ensure_ascii=False) + "\n")

print(f"PROBLEMS={len(problems)} -> {out}")
if problems:
    print("FIRST_ID=", problems[0]["id"])
    print("LAST_ID=", problems[-1]["id"])
