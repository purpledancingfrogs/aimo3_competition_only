import sys, json
from pathlib import Path

bundle = Path(__file__).resolve().parent
solver_path = bundle/"solver.py"
meta_path   = bundle/"kernel-metadata.json"
req_path    = bundle/"requirements.txt"
ov_path     = bundle/"tools"/"runtime_overrides.json"

def slurp(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def hdr(t: str):
    print("\n" + "="*80)
    print(t)
    print("="*80 + "\n")

hdr("PASTE INTO DEEPSEEK / GEMINI (VERBATIM)")

hdr("1) kernel-metadata.json")
print(slurp(meta_path))

hdr("2) solver.py (FULL FILE)")
print(slurp(solver_path))

if req_path.exists():
    hdr("3) requirements.txt")
    print(slurp(req_path))
else:
    hdr("3) requirements.txt (MISSING)")

if ov_path.exists():
    hdr("4) tools/runtime_overrides.json")
    print(slurp(ov_path))
else:
    hdr("4) tools/runtime_overrides.json (MISSING)")

hdr("END PASTE BUNDLE")

hdr("LOCAL HARD GATES")
import py_compile
py_compile.compile(str(solver_path), doraise=True)
print("PY_COMPILE_OK")

sys.path.insert(0, str(bundle))
import solver as S
print("IMPORT_OK")
print("SOLVER_FILE", getattr(S, "__file__", "UNKNOWN"))
print("HAS_SOLVE", hasattr(S, "solve"))
print("HAS_PREDICT", hasattr(S, "predict"))
assert hasattr(S, "solve"), "MISSING solve()"
assert hasattr(S, "predict"), "MISSING predict()"

import polars as pl

df = pl.DataFrame({
    "id":[1],
    "problem":[r"A tournament is held with $2^{20}$ runners each of which has a different running speed. In each race, two runners compete against each other with the faster runner always winning the race. The competition consists of 20 rounds."]
})
sample = pl.DataFrame({"id":[1]})

out1 = S.predict(df, sample)
out2 = S.predict(df)
out3 = S.predict(df, sample_submission=sample)

for out in (out1, out2, out3):
    assert isinstance(out, pl.DataFrame), "predict must return polars.DataFrame"
    assert set(out.columns) == {"id","answer"}, f"bad columns: {out.columns}"
    assert out.height == df.height, "row count mismatch"
    _ = int(out["answer"][0])
    assert str(int(out["answer"][0])).isdigit(), "answer must be digits-only integer"

print("GATEWAY_SHAPES_OK")
