import re, shutil
from pathlib import Path

ROOT = Path.cwd()
TOOLS = ROOT / "tools"
SA = TOOLS / "self_audit.py"
BAK = TOOLS / "self_audit.py.bak_oracle_v1"
SENT = "AUREON_ORACLE_LOGGING_V1"
OUT_REL = "tools/self_audit_oracle_calls.jsonl"

if not SA.exists():
    raise SystemExit(f"NO_SELF_AUDIT: {SA}")

txt = SA.read_text(encoding="utf-8", errors="replace")
if SENT in txt:
    print("ALREADY_PATCHED")
    raise SystemExit(0)

shutil.copyfile(SA, BAK)

lines = txt.splitlines(True)

call_pat = re.compile(r'(?P<pre>^[ \t]*)(?P<expr>.*\b(?:solver\.)?solve\s*\(\s*(?P<arg>.+?)\s*\)\s*)', re.M)

def find_var(lines, idx, indent, kind):
    # scan up to 120 lines upward for a likely variable assigned from row[...] / rec[...] / dict with id/gold keys
    key_re = {
        "gold": re.compile(r"""^(?P<ind>[ \t]*)(?P<var>[A-Za-z_]\w*)\s*=\s*.*(?:row|rec|record|r|item|ex|sample)\s*(?:\[\s*['"](?P<k>[^'"]+)['"]\s*\]|\.get\(\s*['"](?P<k2>[^'"]+)['"])"""),
        "id":   re.compile(r"""^(?P<ind>[ \t]*)(?P<var>[A-Za-z_]\w*)\s*=\s*.*(?:row|rec|record|r|item|ex|sample)\s*(?:\[\s*['"](?P<k>[^'"]+)['"]\s*\]|\.get\(\s*['"](?P<k2>[^'"]+)['"])""")
    }[kind]
    wanted = (("answer","gold","expected","solution","target","label","y","truth") if kind=="gold"
              else ("id","qid","case_id","problem_id","uid"))
    for j in range(max(0, idx-120), idx)[::-1]:
        m = key_re.match(lines[j].rstrip("\n"))
        if not m:
            continue
        ind = m.group("ind")
        if len(ind) > len(indent):  # deeper indent ok
            pass
        elif len(ind) < len(indent):  # left block -> stop
            break
        k = (m.group("k") or m.group("k2") or "").lower()
        if any(w in k for w in wanted):
            return m.group("var")
    return None

patched = []
inject_count = 0

for i, line in enumerate(lines):
    m = call_pat.match(line)
    if not m:
        patched.append(line)
        continue

    indent = m.group("pre")
    arg_expr = m.group("arg").strip()

    gold_var = find_var(lines, i, indent, "gold") or "None"
    id_var   = find_var(lines, i, indent, "id") or "None"

    # inject logging + globals immediately before the solve call line
    inj = []
    inj.append(f"{indent}# {SENT}\n")
    inj.append(f"{indent}try:\n")
    inj.append(f"{indent}    import json as __json\n")
    inj.append(f"{indent}    import solver as __solver\n")
    inj.append(f"{indent}    __solver._SELF_AUDIT_GOLD = {gold_var}\n")
    inj.append(f"{indent}    __solver._SELF_AUDIT_ID = {id_var}\n")
    inj.append(f"{indent}    __p = {arg_expr}\n")
    inj.append(f"{indent}    with open(r\"{OUT_REL}\", \"a\", encoding=\"utf-8\") as __f:\n")
    inj.append(f"{indent}        __f.write(__json.dumps({{\"id\": None if {id_var} is None else str({id_var}), \"gold\": {gold_var}, \"prompt\": \"\" if __p is None else str(__p)}}, ensure_ascii=False) + \"\\n\")\n")
    inj.append(f"{indent}except Exception:\n")
    inj.append(f"{indent}    pass\n")

    patched.extend(inj)
    patched.append(line)
    inject_count += 1

SA.write_text("".join(patched), encoding="utf-8")
print("PATCHED_CALLS", inject_count)
print("BACKUP", str(BAK))
print("ORACLE_OUT", str(ROOT / OUT_REL))