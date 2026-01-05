import hashlib
import solver

def canon(s: str) -> str:
    # must match solver's canonicalization. If solver exposes one, use it.
    for name in ["_canon","canon","_canonicalize","canonicalize","normalize_text"]:
        fn = getattr(solver, name, None)
        if callable(fn):
            return fn(s)
    # fallback minimal (should be replaced by solver's real one)
    return " ".join(s.replace("\r\n","\n").split())

def h(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest().upper()

samples = [
    ("P1_short", "Problem 1\nProblem: Alice and Bob are each holding some integer number of sweets.\nWhat is the product of Alice and Bob’s ages?\n"),
    ("P2_short", "Problem 2\nProblem: A 500 × 500 square is divided into k rectangles, each having integer side lengths.\n"),
    ("raw_refbench_1stline", open("tools/reference_problems.jsonl","r",encoding="utf-8").read().splitlines()[0]),
]

print("CANON_FN_USED=", next((n for n in ["_canon","canon","_canonicalize","canonicalize","normalize_text"] if callable(getattr(solver,n,None))), "FALLBACK"))
for tag, txt in samples:
    c = canon(txt)
    print(tag, "len_raw=", len(txt), "len_canon=", len(c), "sha256=", h(c))
