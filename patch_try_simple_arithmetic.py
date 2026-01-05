import re
from pathlib import Path

p = Path("solver.py")
t = p.read_text(encoding="utf-8")

pat = r"def _try_simple_arithmetic\(s: str\) -> int \| None:\n(?:.*\n)*?(?=\ndef _try_remainder\(|\n\nclass Solver\:|\ndef solve\()"
m = re.search(pat, t)
if not m:
    raise SystemExit("BLOCK_NOT_FOUND")

new_block = """def _try_simple_arithmetic(s: str) -> int | None:
    expr = _extract_arith_candidate(s)
    if not expr:
        return None
    expr = _clean_text(expr)
    if not re.fullmatch(r"[0-9\\+\\-\\*\\/\\(\\)\\.\\s]+", expr):
        return None
    try:
        v = _safe_eval_expr(expr)
        return _safe_int(v)
    except Exception:
        if sp is not None:
            try:
                vv = sp.sympify(expr, locals={"C": sp.binomial, "floor": sp.floor, "ceil": sp.ceiling})
                if vv.is_Number:
                    return _safe_int(vv)
            except Exception:
                pass
        return None
"""

t2 = t[:m.start()] + new_block + t[m.end():]
p.write_text(t2, encoding="utf-8")
print("PATCH_OK")
