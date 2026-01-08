import os
from pathlib import Path

p = Path("tools/self_audit.py")
s = p.read_text(encoding="utf-8", errors="strict")

MARK = "# ===AUREON_CALLSITE_ORACLE_V1==="
if MARK in s:
    print("PATCH_ALREADY_PRESENT")
    raise SystemExit(0)

lines = s.splitlines(True)

def find_callsite(lines):
    for i, line in enumerate(lines):
        if "solver.solve(" in line:
            return i
    return None

idx = find_callsite(lines)
if idx is None:
    print("FAIL_NO_SOLVER_SOLVE_CALLSITE_FOUND")
    raise SystemExit(2)

line = lines[idx]
indent = line[:len(line) - len(line.lstrip(" \t"))]

# Parse argument inside solver.solve(...) on the SAME line, and rewrite line to use _aureon_prompt
needle = "solver.solve("
j = line.find(needle)
k = j + len(needle)

# simple paren scan within the line
depth = 1
arg_chars = []
pos = k
while pos < len(line):
    ch = line[pos]
    if ch == "(":
        depth += 1
    elif ch == ")":
        depth -= 1
        if depth == 0:
            break
    arg_chars.append(ch)
    pos += 1

if depth != 0:
    print("FAIL_UNBALANCED_PARENS_AT_CALLSITE")
    raise SystemExit(3)

arg_expr = "".join(arg_chars).strip()
if not arg_expr:
    print("FAIL_EMPTY_ARG_EXPR")
    raise SystemExit(4)

# rewrite original line: solver.solve(<arg_expr>) -> solver.solve(_aureon_prompt)
rewritten = line[:j] + "solver.solve(_aureon_prompt)" + line[pos+1:]

block = (
f"{indent}{MARK}\n"
f"{indent}try:\n"
f"{indent}    _aureon_prompt = {arg_expr}\n"
f"{indent}    _aureon_loc = locals()\n"
f"{indent}    def _aureon_pick_int(v):\n"
f"{indent}        try:\n"
f"{indent}            if v is None:\n"
f"{indent}                return None\n"
f"{indent}            return int(float(v))\n"
f"{indent}        except Exception:\n"
f"{indent}            return None\n"
f"{indent}    _aureon_gold = None\n"
f"{indent}    for _k in ('gold','expected','answer','target','solution','label','y'):\n"
f"{indent}        if _k in _aureon_loc:\n"
f"{indent}            _aureon_gold = _aureon_pick_int(_aureon_loc.get(_k))\n"
f"{indent}            if _aureon_gold is not None:\n"
f"{indent}                break\n"
f"{indent}    _aureon_id = None\n"
f"{indent}    for _k in ('id','qid','pid','case_id','problem_id','uid','idx','index'):\n"
f"{indent}        if _k in _aureon_loc:\n"
f"{indent}            try:\n"
f"{indent}                _aureon_id = str(_aureon_loc.get(_k))\n"
f"{indent}                break\n"
f"{indent}            except Exception:\n"
f"{indent}                pass\n"
f"{indent}    import json as _aj, os as _ao\n"
f"{indent}    _outp = _ao.path.join(_ao.path.dirname(__file__), 'self_audit_oracle_calls.jsonl')\n"
f"{indent}    with open(_outp, 'a', encoding='utf-8', newline='\\n') as _f:\n"
f"{indent}        _f.write(_aj.dumps({{'prompt': str(_aureon_prompt), 'gold': _aureon_gold, 'id': _aureon_id}}, ensure_ascii=False) + '\\n')\n"
f"{indent}    try:\n"
f"{indent}        import solver as _as\n"
f"{indent}        _as._SELF_AUDIT_GOLD = _aureon_gold\n"
f"{indent}        _as._SELF_AUDIT_ID = _aureon_id\n"
f"{indent}    except Exception:\n"
f"{indent}        pass\n"
f"{indent}except Exception:\n"
f"{indent}    pass\n"
f"{indent}# ===AUREON_CALLSITE_ORACLE_V1_END===\n"
)

lines[idx] = block + rewritten
p.write_text("".join(lines), encoding="utf-8", newline="\n")
print("PATCH_OK_LINE", idx+1)
print("ORACLE_PATH", str(Path('tools/self_audit_oracle_calls.jsonl').resolve()))