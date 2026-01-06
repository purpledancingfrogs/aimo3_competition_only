import re
import polars as pl

# AUREON_PATHFIX
import os as _os, sys as _sys
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _ROOT not in _sys.path: _sys.path.insert(0, _ROOT)

I64_MIN = -(2**63)
I64_MAX =  (2**63 - 1)

_int_re = re.compile(r"[-+]?\d+")

def _to_i64(x) -> int:
    try:
        if x is None:
            return 0
        if isinstance(x, int):
            v = x
        else:
            s = str(x).strip()
            m = _int_re.search(s)
            if not m:
                return 0
            v = int(m.group(0))
        if v < I64_MIN or v > I64_MAX:
            return 0
        return v
    except Exception:
        return 0

class AIMO3Gateway:
    def __init__(self):
        from solver import solve
        self._solve = solve

    def predict(self, df: pl.DataFrame) -> pl.DataFrame:
        probs = df["problem"].to_list()
        outs = []
        for p in probs:
            try:
                ans = self._solve(str(p))
            except Exception:
                ans = 0
            outs.append(_to_i64(ans))
        return pl.DataFrame({"answer": pl.Series("answer", outs, dtype=pl.Int64)})
