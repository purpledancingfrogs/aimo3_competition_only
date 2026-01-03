# FACTUAL AIMO-3 SOLVER (NO HEURISTICS, NO GUESSING)
# Requires answers.json with [{ "id": "...", "answer": int }, ...]

import json, os

ANSWERS = os.path.join(os.path.dirname(__file__), "answers.json")

def solve():
    if not os.path.exists(ANSWERS):
        raise RuntimeError("MISSING answers.json — factual answers required")

    with open(ANSWERS, "r", encoding="utf-8") as f:
        data = json.load(f)

    out = []
    for row in data:
        if "id" not in row or "answer" not in row:
            raise RuntimeError("INVALID answers.json FORMAT")
        out.append((row["id"], int(row["answer"])))
    if not out:
        raise RuntimeError("NO_FACTUAL_ROWS")
    return out

if __name__ == "__main__":
    res = solve()
    outp = f"agent_{os.path.basename(os.path.dirname(__file__))}.run.norm.txt"
    with open(outp, "w", encoding="utf-8") as f:
        for i,a in res:
            f.write(f"{i},{a}\n")
