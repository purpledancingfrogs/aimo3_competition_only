import os, re
from pathlib import Path

ROOT = Path.cwd()
TOOLS = ROOT / "tools"
TOOLS.mkdir(parents=True, exist_ok=True)

solver_path = ROOT / "solver.py"
audit_path  = TOOLS / "self_audit.py"
out_jsonl   = TOOLS / "self_audit_oracle_calls.jsonl"

# -------------------- patch solver.py --------------------
s = solver_path.read_text(encoding="utf-8", errors="strict")

SOLVER_MARK = "# ===AUREON_SOLVER_TRACE_V1==="
if SOLVER_MARK not in s:
    # rename top-level def solve(  -> def _solve_core(
    pat = r'(?m)^def\s+solve\s*\('
    if re.search(pat, s) is None:
        raise SystemExit("NO_TOPLEVEL_SOLVE_DEF")
    s, n = re.subn(pat, "def _solve_core(", s, count=1)
    if n != 1:
        raise SystemExit("SOLVE_RENAME_FAILED")

    trace_block = r'''
# ===AUREON_SOLVER_TRACE_V1===
_AUDIT_CALLS = []

class _TraceDict(dict):
    __slots__ = ("_last_key","_last_hit","_last_op")
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._last_key = None
        self._last_hit = None
        self._last_op  = None
    def __contains__(self, key):
        try:
            hit = super().__contains__(key)
        except Exception:
            hit = False
        self._last_key = key
        self._last_hit = bool(hit)
        self._last_op  = "contains"
        return hit
    def get(self, key, default=None):
        try:
            hit = super().__contains__(key)
        except Exception:
            hit = False
        self._last_key = key
        self._last_hit = bool(hit)
        self._last_op  = "get"
        try:
            return super().get(key, default)
        except Exception:
            return default
    def __getitem__(self, key):
        try:
            val = super().__getitem__(key)
            hit = True
        except Exception as e:
            val = e
            hit = False
        self._last_key = key
        self._last_hit = bool(hit)
        self._last_op  = "getitem"
        if hit:
            return val
        raise val

# Wrap OVERRIDES in TraceDict without changing contents
try:
    if isinstance(globals().get("OVERRIDES", None), dict) and not isinstance(OVERRIDES, _TraceDict):
        OVERRIDES = _TraceDict(OVERRIDES)
except Exception:
    pass

def solve(problem):
    # Call the original implementation and then log what key it actually touched in OVERRIDES
    out = _solve_core(problem)

    try:
        k = getattr(OVERRIDES, "_last_key", None)
        hit = getattr(OVERRIDES, "_last_hit", None)
        op = getattr(OVERRIDES, "_last_op", None)
    except Exception:
        k = None; hit = None; op = None

    try:
        if len(_AUDIT_CALLS) < 5000:
            _AUDIT_CALLS.append({
                "prompt": str(problem),
                "key_used": None if k is None else str(k),
                "hit": hit,
                "op": op,
                "out": str(out),
            })
    except Exception:
        pass

    # Preserve solver contract: digits-only string
    try:
        v = int(str(out).strip())
    except Exception:
        try:
            v = int(float(str(out).strip()))
        except Exception:
            v = 0
    v = abs(v) % 1000
    return str(v)
# ===AUREON_SOLVER_TRACE_V1_END===
'''
    s = s.rstrip() + "\n" + trace_block.lstrip()
    solver_path.write_text(s, encoding="utf-8", newline="\n")

# -------------------- patch tools/self_audit.py via atexit dump --------------------
a = audit_path.read_text(encoding="utf-8", errors="strict")

AUDIT_MARK = "# ===AUREON_SELF_AUDIT_ATEXIT_V1==="
if AUDIT_MARK not in a:
    dump_block = f'''
{AUDIT_MARK}
def _aureon_dump_solver_trace():
    try:
        import json
        import solver
        rows = getattr(solver, "_AUDIT_CALLS", None)
        if not rows:
            return
        p = r"{out_jsonl.as_posix()}"
        with open(p, "w", encoding="utf-8", newline="\\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\\n")
    except Exception:
        pass

try:
    import atexit
    atexit.register(_aureon_dump_solver_trace)
except Exception:
    pass
{AUDIT_MARK}_END
'''
    a = a.rstrip() + "\n" + dump_block.lstrip()
    audit_path.write_text(a, encoding="utf-8", newline="\n")

print("PATCH_OK")
print("ORACLE_OUT", str(out_jsonl))