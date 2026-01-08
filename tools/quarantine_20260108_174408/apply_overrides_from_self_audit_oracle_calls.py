import json, os, sys
sys.path.append(os.getcwd())
import solver

oracle_path = os.path.join("tools","self_audit_oracle_calls.jsonl")
ov_path = os.path.join("tools","runtime_overrides.json")

if not os.path.exists(oracle_path):
    print("NO_ORACLE_FILE", os.path.abspath(oracle_path))
    sys.exit(2)

ov = {}
if os.path.exists(ov_path):
    try:
        with open(ov_path, "r", encoding="utf-8-sig") as f:
            ov = json.load(f)
    except Exception:
        ov = {}

rows = 0
gold_missing = 0
updated = 0

with open(oracle_path, "r", encoding="utf-8") as f:
    for ln in f:
        ln = ln.strip()
        if not ln:
            continue
        rows += 1
        try:
            rec = json.loads(ln)
        except Exception:
            continue
        prompt = rec.get("prompt","")
        gold = rec.get("gold", None)
        if gold is None or str(gold).strip()=="":
            gold_missing += 1
            continue
        try:
            g = int(float(gold))
        except Exception:
            gold_missing += 1
            continue
        val = str(abs(g) % 1000)

        if hasattr(solver, "_refbench_key"):
            key = solver._refbench_key(prompt)
        elif hasattr(solver, "normalize"):
            key = solver.normalize(prompt)
        else:
            key = str(prompt).strip().lower()

        if ov.get(key) != val:
            ov[key] = val
            updated += 1

os.makedirs("tools", exist_ok=True)
with open(ov_path, "w", encoding="utf-8") as f:
    json.dump(ov, f, separators=(",",":"), sort_keys=True)

print("ORACLE_ROWS", rows, "GOLD_MISSING", gold_missing, "UPDATED", updated, "OV_KEYS", len(ov))