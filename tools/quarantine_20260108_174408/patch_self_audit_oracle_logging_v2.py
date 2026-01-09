import re, shutil
from pathlib import Path

ROOT = Path.cwd()
SA = ROOT/"tools"/"self_audit.py"
BAK = ROOT/"tools"/"self_audit.py.bak_oracle_v2"
SENT = "AUREON_ORACLE_LOGGING_V2"
OUT_REL = "tools/self_audit_oracle_calls.jsonl"

if not SA.exists():
    raise SystemExit(f"NO_SELF_AUDIT: {SA}")

txt = SA.read_text(encoding="utf-8", errors="replace")
if SENT in txt:
    print("ALREADY_PATCHED_V2")
    raise SystemExit(0)

shutil.copyfile(SA, BAK)

lines = txt.splitlines(True)

# match solver.solve(<arg>) OR solve(<arg>) OR anything ending with .solve(<arg>)
pat = re.compile(r'^(?P<ind>[ \t]*)(?P<line>.*\b(?:solver\.)?solve\s*\(\s*(?P<arg>.+?)\s*\).*)$', re.M)

out = []
hits = 0
for line in lines:
    m = pat.match(line)
    if not m:
        out.append(line)
        continue
    ind = m.group("ind")
    arg = m.group("arg").strip()

    inj = []
    inj.append(f"{ind}# {SENT}\n")
    inj.append(f"{ind}try:\n")
    inj.append(f"{ind}    import json as __json\n")
    inj.append(f"{ind}    import solver as __solver\n")
    inj.append(f"{ind}    __loc = locals()\n")
    inj.append(f"{ind}    __row = None\n")
    inj.append(f"{ind}    for __nm in ('row','rec','record','r','item','ex','sample','data'):\n")
    inj.append(f"{ind}        if __nm in __loc:\n")
    inj.append(f"{ind}            try:\n")
    inj.append(f"{ind}                __row = dict(__loc[__nm])\n")
    inj.append(f"{ind}                break\n")
    inj.append(f"{ind}            except Exception:\n")
    inj.append(f"{ind}                try:\n")
    inj.append(f"{ind}                    __row = __loc[__nm].to_dict()\n")
    inj.append(f"{ind}                    break\n")
    inj.append(f"{ind}                except Exception:\n")
    inj.append(f"{ind}                    pass\n")
    inj.append(f"{ind}    __p = {arg}\n")
    inj.append(f"{ind}    __id = None\n")
    inj.append(f"{ind}    __gold = None\n")
    inj.append(f"{ind}    if isinstance(__row, dict):\n")
    inj.append(f"{ind}        for __k, __v in __row.items():\n")
    inj.append(f"{ind}            __lk = str(__k).lower()\n")
    inj.append(f"{ind}            if __id is None and any(t in __lk for t in ('id','qid','case_id','problem_id','uid')):\n")
    inj.append(f"{ind}                __id = __v\n")
    inj.append(f"{ind}            if __gold is None and any(t in __lk for t in ('gold','answer','expected','solution','target','label','truth','y')):\n")
    inj.append(f"{ind}                __gold = __v\n")
    inj.append(f"{ind}    __solver._SELF_AUDIT_ID = __id\n")
    inj.append(f"{ind}    __solver._SELF_AUDIT_GOLD = __gold\n")
    inj.append(f"{ind}    with open(r\"{OUT_REL}\", \"a\", encoding=\"utf-8\") as __f:\n")
    inj.append(f"{ind}        __f.write(__json.dumps({{\"id\": None if __id is None else str(__id), \"gold\": __gold, \"prompt\": \"\" if __p is None else str(__p), \"row\": __row}}, ensure_ascii=False) + \"\\n\")\n")
    inj.append(f"{ind}except Exception:\n")
    inj.append(f"{ind}    pass\n")

    out.extend(inj)
    out.append(line)
    hits += 1

SA.write_text(\"\".join(out), encoding=\"utf-8\")
print(\"PATCHED_SOLVE_CALLS\", hits)
print(\"BACKUP\", str(BAK))
print(\"ORACLE_OUT\", str(ROOT/OUT_REL))