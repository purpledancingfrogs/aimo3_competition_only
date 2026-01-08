import os, re, sys, time

SELF_AUDIT = os.path.join("tools","self_audit.py")
SENT_BEGIN = "# ORACLE_CALL_LOG_BEGIN"
SENT_END   = "# ORACLE_CALL_LOG_END"

def read_text(p):
    with open(p, "r", encoding="utf-8-sig", newline="") as f:
        return f.read()

def write_text(p, s):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)

def extract_arg(line, start_idx):
    # scan for matching ')' with nesting
    depth = 0
    out = []
    for ch in line[start_idx:]:
        if ch == "(":
            depth += 1
            out.append(ch)
        elif ch == ")":
            if depth == 0:
                break
            depth -= 1
            out.append(ch)
        else:
            out.append(ch)
    return "".join(out).strip()

src = read_text(SELF_AUDIT)
if SENT_BEGIN in src and SENT_END in src:
    print("PATCH_ALREADY_PRESENT")
    sys.exit(0)

lines = src.splitlines(True)

call_idx = None
arg_expr = None
for i, ln in enumerate(lines):
    if "solver.solve(" in ln:
        call_idx = i
        s = ln.find("solver.solve(") + len("solver.solve(")
        arg_expr = extract_arg(ln, s)
        break

if call_idx is None or not arg_expr:
    print("FAIL_NO_SOLVER_SOLVE_CALL_FOUND")
    sys.exit(2)

indent = re.match(r"^(\s*)", lines[call_idx]).group(1)

# backup
bak = SELF_AUDIT + f".bak_{int(time.time())}"
with open(bak, "wb") as f:
    f.write(src.encode("utf-8", errors="ignore"))

inject = []
inject.append(indent + SENT_BEGIN + "\n")
inject.append(indent + "try:\n")
inject.append(indent + "    import json, os\n")
inject.append(indent + "    _oracle_path = os.path.join(os.path.dirname(__file__), 'self_audit_oracle_calls.jsonl')\n")
inject.append(indent + "    _loc = locals()\n")
inject.append(indent + "    _gold = _loc.get('gold', _loc.get('expected', _loc.get('answer', _loc.get('target', _loc.get('solution', _loc.get('label', None))))))\n")
inject.append(indent + "    _pid  = _loc.get('id', _loc.get('pid', _loc.get('problem_id', _loc.get('row_id', _loc.get('qid', _loc.get('idx', _loc.get('i', None)))))))\n")
inject.append(indent + "    try:\n")
inject.append(indent + "        solver._SELF_AUDIT_GOLD = _gold\n")
inject.append(indent + "        solver._SELF_AUDIT_ID = _pid\n")
inject.append(indent + "    except Exception:\n")
inject.append(indent + "        pass\n")
inject.append(indent + f"    _prompt = ({arg_expr})\n")
inject.append(indent + "    _row = {'prompt': str(_prompt), 'gold': _gold, 'id': _pid}\n")
inject.append(indent + "    with open(_oracle_path, 'a', encoding='utf-8') as _f:\n")
inject.append(indent + "        _f.write(json.dumps(_row, ensure_ascii=False) + '\\n')\n")
inject.append(indent + "except Exception:\n")
inject.append(indent + "    pass\n")
inject.append(indent + SENT_END + "\n")

lines[call_idx:call_idx] = inject
write_text(SELF_AUDIT, "".join(lines))

print("PATCH_OK_AT_LINE", call_idx+1)
print("BACKUP", bak)
print("ORACLE_PATH", os.path.abspath(os.path.join('tools','self_audit_oracle_calls.jsonl')))