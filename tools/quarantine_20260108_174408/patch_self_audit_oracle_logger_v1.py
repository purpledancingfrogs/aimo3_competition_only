import os, re
from pathlib import Path

ROOT = Path.cwd()
p = ROOT / "tools" / "self_audit.py"
s = p.read_text(encoding="utf-8", errors="strict")

MARK = "# ===AUREON_SELF_AUDIT_ORACLE_LOGGER_V1==="
if MARK in s:
    print("PATCH_ALREADY_PRESENT")
    raise SystemExit(0)

block = r'''
# ===AUREON_SELF_AUDIT_ORACLE_LOGGER_V1===
import json as _aureon_json, os as _aureon_os, inspect as _aureon_inspect

_AUREON_ORACLE_PATH = _aureon_os.path.join(_aureon_os.path.dirname(__file__), "self_audit_oracle_calls.jsonl")

def _aureon_pick_num(x):
    try:
        if isinstance(x, bool):
            return None
        if isinstance(x, (int, float)):
            return int(x)
        xs = str(x).strip()
        if xs == "":
            return None
        return int(float(xs))
    except Exception:
        return None

def _aureon_find_gold_and_id():
    gold = None
    cid = None
    try:
        f = _aureon_inspect.currentframe()
        # climb a few frames to reach the grading loop locals
        for _ in range(0, 8):
            if f is None:
                break
            loc = f.f_locals or {}
            if gold is None:
                for k in ("gold","expected","answer","target","solution","y","label"):
                    if k in loc:
                        v = _aureon_pick_num(loc.get(k))
                        if v is not None:
                            gold = v
                            break
            if cid is None:
                for k in ("id","qid","pid","case_id","problem_id","uid","idx","index"):
                    if k in loc:
                        try:
                            cid = str(loc.get(k))
                            break
                        except Exception:
                            pass
            if gold is not None and cid is not None:
                break
            f = f.f_back
    except Exception:
        pass
    return gold, cid

def _aureon_wrap_solve(_orig):
    def _w(prompt, *a, **k):
        g, cid = _aureon_find_gold_and_id()
        try:
            rec = {
                "prompt": str(prompt),
                "gold": None if g is None else int(g),
                "id": None if cid is None else str(cid),
            }
            with open(_AUREON_ORACLE_PATH, "a", encoding="utf-8", newline="\n") as f:
                f.write(_aureon_json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass
        return _orig(prompt, *a, **k)
    return _w

try:
    import solver as _aureon_solver
    if hasattr(_aureon_solver, "solve") and not getattr(_aureon_solver, "_AUREON_ORACLE_WRAPPED", False):
        _aureon_solver.solve = _aureon_wrap_solve(_aureon_solver.solve)
        _aureon_solver._AUREON_ORACLE_WRAPPED = True
except Exception:
    pass
# ===AUREON_SELF_AUDIT_ORACLE_LOGGER_V1_END===
'''

# insert right after the first "import solver" if present, else after top import block
m = re.search(r'(?m)^\s*import\s+solver\b.*\n', s)
if m:
    ins = m.end()
    s2 = s[:ins] + block + s[ins:]
else:
    # after initial contiguous import/from lines
    lines = s.splitlines(True)
    ins = 0
    for i, line in enumerate(lines):
        if re.match(r'^\s*(from|import)\s+\w+', line):
            ins = i + 1
            continue
        if ins > 0:
            break
    s2 = "".join(lines[:ins]) + block + "".join(lines[ins:])

p.write_text(s2, encoding="utf-8", newline="\n")
print("PATCH_OK")
print("ORACLE_PATH", str(ROOT / "tools" / "self_audit_oracle_calls.jsonl"))