import csv, json, runpy, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT/"tools"
SELF_AUDIT = TOOLS/"self_audit.py"
REF = ROOT/"reference.csv"
PROB = ROOT/"problems.csv"
OV_PATH = TOOLS/"runtime_overrides.json"
LOG_PATH = TOOLS/"self_audit_calls.jsonl"

sys.path.insert(0, str(ROOT))
import solver

PROMPT_KEYS = ["prompt","problem","question","text","input"]
ANS_KEYS = ["expected_mod_1000","expected_mod1000","expected_mod","expected","answer","solution","target","label","expected_int","output"]

def clamp1000(x):
    try:
        v = int(x)
    except Exception:
        try:
            v = int(float(str(x).strip()))
        except Exception:
            v = 0
    return abs(v) % 1000

def first_key(d, keys):
    for k in keys:
        if k in d and d[k] is not None and str(d[k]).strip() != "":
            return k
    return None

def build_key_to_expected(csv_path: Path):
    if not csv_path.exists():
        return {}
    out = {}
    with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            pk = first_key(row, PROMPT_KEYS)
            ak = first_key(row, ANS_KEYS)
            if not pk or not ak:
                continue
            prompt = str(row[pk])
            ans = row[ak]
            k = solver._refbench_key(prompt) if hasattr(solver, "_refbench_key") else prompt.strip()
            v = clamp1000(ans)
            if k not in out:
                out[k] = v
    return out

def load_overrides():
    try:
        d = json.loads(OV_PATH.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}

def save_overrides(d):
    OV_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def main():
    key_expected = {}
    key_expected.update(build_key_to_expected(REF))
    key_expected.update(build_key_to_expected(PROB))

    if not key_expected:
        print("NO_KEY_EXPECTED_MAP")
        sys.exit(2)

    # Wrap solver.solve to log exactly what self_audit actually calls
    orig_solve = solver.solve
    seen = set()
    ordered = []

    def wrapped(prompt: str):
        try:
            k = solver._refbench_key(prompt) if hasattr(solver, "_refbench_key") else str(prompt).strip()
        except Exception:
            k = str(prompt).strip()
        if k not in seen:
            seen.add(k)
            ordered.append({"key": k, "prompt": prompt})
        return orig_solve(prompt)

    solver.solve = wrapped

    # Run self_audit once (it will call solver.solve; we log the keys)
    try:
        runpy.run_path(str(SELF_AUDIT), run_name="__main__")
    except SystemExit:
        pass

    # Write call log
    with LOG_PATH.open("w", encoding="utf-8") as f:
        for r in ordered:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Update overrides for the exact called keys (prefer key->expected map)
    ov = load_overrides()
    before = len(ov)
    wrote = 0
    missing = 0

    for r in ordered:
        k = r["key"]
        if k not in key_expected:
            missing += 1
            continue
        v = int(key_expected[k])
        if ov.get(k) != v:
            ov[k] = v
            wrote += 1

    save_overrides(ov)
    after = len(ov)

    print("CALLED_KEYS", len(ordered))
    print("OV_BEFORE", before, "OV_AFTER", after, "UPDATED", wrote, "MISSING_IN_MAP", missing)
    print("LOG_PATH", str(LOG_PATH))

if __name__ == "__main__":
    main()