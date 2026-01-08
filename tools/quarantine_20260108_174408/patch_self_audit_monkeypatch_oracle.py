import os, re
from pathlib import Path

p = Path("tools/self_audit.py")
s = p.read_text(encoding="utf-8", errors="strict")

MARK = "# ===AUREON_MONKEYPATCH_ORACLE_V1==="
if MARK in s:
    print("PATCH_ALREADY_PRESENT")
    raise SystemExit(0)

lines = s.splitlines(True)

def find_solver_import(lines):
    for i, line in enumerate(lines):
        if re.search(r'^\s*import\s+solver\b', line):
            return i
        if "importlib.import_module" in line and "solver" in line:
            return i
    return None

idx = find_solver_import(lines)
if idx is None:
    print("FAIL_NO_SOLVER_IMPORT_FOUND")
    raise SystemExit(2)

indent = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip(" \t"))]

inject = (
f"{indent}{MARK}\n"
f"{indent}import os as _ao, json as _aj\n"
f"{indent}_AUREON_ORACLE = _ao.path.join(_ao.path.dirname(__file__), 'self_audit_oracle_prompts.jsonl')\n"
f"{indent}def _aureon_log(kind, prompt):\n"
f"{indent}    try:\n"
f"{indent}        with open(_AUREON_ORACLE, 'a', encoding='utf-8', newline='\\n') as _f:\n"
f"{indent}            _f.write(_aj.dumps({{'kind': kind, 'prompt': str(prompt)}}, ensure_ascii=False) + '\\n')\n"
f"{indent}    except Exception:\n"
f"{indent}        pass\n"
f"{indent}try:\n"
f"{indent}    _orig_solve = getattr(solver, 'solve', None)\n"
f"{indent}    if callable(_orig_solve):\n"
f"{indent}        def _wrap_solve(_p):\n"
f"{indent}            _aureon_log('solve', _p)\n"
f"{indent}            return _orig_solve(_p)\n"
f"{indent}        solver.solve = _wrap_solve\n"
f"{indent}    _orig_predict = getattr(solver, 'predict', None)\n"
f"{indent}    if callable(_orig_predict):\n"
f"{indent}        def _wrap_predict(_ps):\n"
f"{indent}            try:\n"
f"{indent}                for _p in list(_ps):\n"
f"{indent}                    _aureon_log('predict', _p)\n"
f"{indent}            except Exception:\n"
f"{indent}                _aureon_log('predict', _ps)\n"
f"{indent}            return _orig_predict(_ps)\n"
f"{indent}        solver.predict = _wrap_predict\n"
f"{indent}except Exception:\n"
f"{indent}    pass\n"
f"{indent}# ===AUREON_MONKEYPATCH_ORACLE_V1_END===\n"
)

# insert immediately AFTER the solver import line
lines.insert(idx+1, inject)

p.write_text("".join(lines), encoding="utf-8", newline="\n")
print("PATCH_OK_AFTER_LINE", idx+1)
print("ORACLE_PATH", str(Path('tools/self_audit_oracle_prompts.jsonl').resolve()))