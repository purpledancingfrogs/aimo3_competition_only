import re
import polars as pl
import io
import contextlib

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
    def __init__(self, data_paths=None):
        self._data_paths = data_paths
        from solver import solve
        self._solve = solve

    def predict(self, df: pl.DataFrame) -> pl.DataFrame:
        probs = df["problem"].to_list()
        outs = []
        for p in probs:
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                  ans = self._solve(str(p))
            except Exception:
                ans = 0
            outs.append(_to_i64(ans))
                # Contract: return DataFrame with columns exactly ['id','answer'] and row-aligned.
        def _clamp_str(x):
            s = str(x).strip()
            try:
                v = int(s)
            except Exception:
                v = 0
            if v < 0: v = 0
            if v > 99999: v = 99999
            return str(v)
        ans = [ _clamp_str(x) for x in outs ]
        ids = df['id'] if 'id' in df.columns else pl.Series('id', list(range(len(ans))))
        return pl.DataFrame({'id': ids, 'answer': pl.Series('answer', ans, dtype=pl.Utf8)})
