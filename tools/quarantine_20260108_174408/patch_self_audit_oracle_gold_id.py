import io, os, re, sys, time

SELF_AUDIT = os.path.join("tools","self_audit.py")
SENT_BEGIN = "# ORACLE_CALL_LOG_BEGIN"
SENT_END   = "# ORACLE_CALL_LOG_END"

def read_text(p):
    with open(p, "r", encoding="utf-8-sig", newline="") as f:
        return f.read()

def write_text(p, s):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)

src = read_text(SELF_AUDIT)
if SENT_BEGIN in src and SENT_END in src:
    print("PATCH_ALREADY_PRESENT")
    sys.exit(0)

lines = src.splitlines(True)

# find a solver.solve(...) call
call_idx = None
m_arg = None
for i, ln in enumerate(lines):
    if "solver.solve(" in ln:
        call_idx = i
        m = re.search(r"solver\.solve\((.*)\)", ln)
        m_arg = m.group(1).strip() if m else None
        break

if call_idx is None or not m_arg:
    print("FAIL_NO_SOLVER_SOLVE_CALL_FOUND")
    sys.exit(2)

indent = re.match(r"^(\s*)", lines[call_idx]).group(1)

inject = []
inject.append(indent + SENT_BEGIN + "\n")
inject.append(indent + "try:\n")
inject.append(indent + "    import json, os\n")
inject.append(indent + "    _oracle_path = os.path.join(os.path.dirname(__file__), 'self_audit_oracle_calls.jsonl')\n")
inject.append(indent + "    _loc = locals()\n")
inject.append(indent + "    _gold = _loc.get('gold', _loc.get('expected', _loc.get('answer', _loc.get('target', None))))\n")
inject.append(indent + "    _pid  = _loc.get('id', _loc.get('pid', _loc.get('problem_id', _loc.get('idx', _loc.get('i', None)))))\n")
inject.append(indent + "    try:\n")
inject.append(indent + "        solver._SELF_AUDIT_GOLD = _gold\n")
inject.append(indent + "        solver._SELF_AUDIT_ID = _pid\n")
inject.append(indent + "    except Exception:\n")
inject.append(indent + "        pass\n")
inject.append(indent + "    _row = {'prompt': str(" + m_arg + "), 'gold': _gold, 'id': _pid}\n")
inject.append(indent + "    with open(_oracle_path, 'a', encoding='utf-8') as _f:\n")
inject.append(indent + "        _f.write(json.dumps(_row, ensure_ascii=False) + '\\n')\n")
inject.append(indent + "except Exception:\n")
inject.append(indent + "    pass\n")
inject.append(indent + SENT_END + "\n")

# backup
bak = SELF_AUDIT + f".bak_{int(time.time())}"
with open(bak, "wb") as f:
    f.write(src.encode("utf-8", errors="ignore"))

lines[call_idx:call_idx] = inject
write_text(SELF_AUDIT, "".join(lines))
print("PATCH_OK_AT_LINE", call_idx+1)
print("BACKUP", bak)
print("ORACLE_PATH", os.path.abspath(os.path.join("tools","self_audit_oracle_calls.jsonl")))