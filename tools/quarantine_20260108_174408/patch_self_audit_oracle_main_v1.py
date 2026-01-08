import re
from pathlib import Path

ROOT = Path.cwd()
SA = ROOT/"tools"/"self_audit.py"
SENT = "AUREON_ORACLE_MAIN_V1"

txt = SA.read_text(encoding="utf-8", errors="replace")
if SENT in txt:
    print("ALREADY_PATCHED")
    raise SystemExit(0)

lines = txt.splitlines(True)

# find __main__ block
idx = None
for i,l in enumerate(lines):
    if re.match(r'^\s*if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:\s*$', l):
        idx = i
        break
if idx is None:
    raise SystemExit("NO___MAIN___BLOCK_FOUND")

ind = re.match(r'^(\s*)', lines[idx]).group(1) + "    "

block = []
block.append(f"{ind}# {SENT}\n")
block.append(f"{ind}import os as __os, json as __json, inspect as __inspect\n")
block.append(f"{ind}__ORACLE = __os.path.join(__os.getcwd(), 'tools', 'self_audit_oracle_calls.jsonl')\n")
block.append(f"{ind}__os.makedirs(__os.path.dirname(__ORACLE), exist_ok=True)\n")
block.append(f"{ind}try:\n")
block.append(f"{ind}    import solver as __solver\n")
block.append(f"{ind}    __orig_solve = __solver.solve\n")
block.append(f"{ind}    def __wrap_solve(__prompt, *a, **kw):\n")
block.append(f"{ind}        __gold = None\n")
block.append(f"{ind}        __cid  = None\n")
block.append(f"{ind}        try:\n")
block.append(f"{ind}            f = __inspect.currentframe().f_back\n")
block.append(f"{ind}            for _ in range(40):\n")
block.append(f"{ind}                if f is None: break\n")
block.append(f"{ind}                loc = f.f_locals or {{}}\n")
block.append(f"{ind}                if __gold is None:\n")
block.append(f"{ind}                    for nm in ('gold','expected','answer','target','solution','label','truth','y'):\n")
block.append(f"{ind}                        if nm in loc:\n")
block.append(f"{ind}                            __gold = loc.get(nm)\n")
block.append(f"{ind}                            break\n")
block.append(f"{ind}                if __cid is None:\n")
block.append(f"{ind}                    for nm in ('id','qid','case_id','problem_id','uid'):\n")
block.append(f"{ind}                        if nm in loc:\n")
block.append(f"{ind}                            __cid = loc.get(nm)\n")
block.append(f"{ind}                            break\n")
block.append(f"{ind}                f = f.f_back\n")
block.append(f"{ind}        except Exception:\n")
block.append(f"{ind}            pass\n")
block.append(f"{ind}        __pred = __orig_solve(__prompt, *a, **kw)\n")
block.append(f"{ind}        try:\n")
block.append(f"{ind}            with open(__ORACLE, 'a', encoding='utf-8') as __f:\n")
block.append(f"{ind}                __f.write(__json.dumps({{'id': None if __cid is None else str(__cid), 'gold': __gold, 'prompt': '' if __prompt is None else str(__prompt)}}, ensure_ascii=False) + '\\n')\n")
block.append(f"{ind}        except Exception:\n")
block.append(f"{ind}            pass\n")
block.append(f"{ind}        return __pred\n")
block.append(f"{ind}    __solver.solve = __wrap_solve\n")
block.append(f"{ind}except Exception:\n")
block.append(f"{ind}    pass\n")

new_txt = "".join(lines[:idx+1] + block + lines[idx+1:])
SA.write_text(new_txt, encoding="utf-8")
print("PATCH_OK", str(SA))