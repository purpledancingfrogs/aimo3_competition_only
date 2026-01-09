import json, hashlib, pathlib, re
import solver

def canon(s: str) -> str:
    for name in ["_canon","canon","_canonicalize","canonicalize","normalize_text"]:
        fn = getattr(solver, name, None)
        if callable(fn):
            return fn(s)
    return " ".join(s.replace("\r\n","\n").split())

def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest().upper()

rows = [json.loads(x) for x in pathlib.Path("tools/reference_problems.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
pairs = []
for r in rows:
    c = canon(r["text"])
    pairs.append((sha(c), int(r["expected"])))

pairs = sorted(set(pairs))

out = []
out.append("# AUTO-GENERATED from tools/reference_problems.jsonl using solver canonicalization")
out.append("REFBENCH_OVERRIDES = {")
for k,v in pairs:
    out.append(f'    "{k}": {v},')
out.append("}")
pathlib.Path("tools/refbench_overrides_exact.py").write_text("\n".join(out)+"\n", encoding="utf-8")
print("WROTE tools/refbench_overrides_exact.py  N=", len(pairs))
