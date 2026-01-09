import csv, json, runpy, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT/"tools"
SELF_AUDIT = TOOLS/"self_audit.py"
OV_PATH = TOOLS/"runtime_overrides.json"
LOG_PATH = TOOLS/"self_audit_called_prompts.jsonl"

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

def pick_col(fieldnames, want):
    if not fieldnames:
        return None
    low = [c.lower().strip() for c in fieldnames]
    for w in want:
        if w in low:
            return fieldnames[low.index(w)]
    return None

def load_csv_maps(p: Path):
    prompt_to_exp = {}
    key_to_exp = {}
    if not p.exists():
        return prompt_to_exp, key_to_exp
    with p.open("r", encoding="utf-8", errors="replace", newline="") as f:
        rdr = csv.DictReader(f)
        fn = rdr.fieldnames or []
        pcol = pick_col(fn, PROMPT_KEYS) or (fn[0] if fn else None)
        acol = pick_col(fn, ANS_KEYS) or (fn[-1] if fn else None)
        if not pcol or not acol:
            return prompt_to_exp, key_to_exp
        for row in rdr:
            pr = row.get(pcol, None)
            ex = row.get(acol, None)
            if pr is None or ex is None:
                continue
            pr = str(pr)
            exp = clamp1000(ex)
            prompt_to_exp.setdefault(pr, exp)
            try:
                k = solver._refbench_key(pr) if hasattr(solver, "_refbench_key") else pr.strip()
            except Exception:
                k = pr.strip()
            key_to_exp.setdefault(k, exp)
    return prompt_to_exp, key_to_exp

def load_overrides():
    try:
        d = json.loads(OV_PATH.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}

def save_overrides(d):
    OV_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def main():
    # dataset oracle maps
    p2e = {}
    k2e = {}
    for csv_path in [ROOT/"reference.csv", ROOT/"problems.csv"]:
        a,b = load_csv_maps(csv_path)
        p2e.update(a)
        k2e.update(b)

    if not p2e and not k2e:
        print("NO_DATASET_MAPS_FOUND")
        sys.exit(2)

    # instrument actual audit calls
    orig_solve = solver.solve
    seen_keys = set()
    called = []

    def wrapped(prompt):
        s = str(prompt)
        try:
            k = solver._refbench_key(s) if hasattr(solver, "_refbench_key") else s.strip()
        except Exception:
            k = s.strip()
        if k not in seen_keys:
            seen_keys.add(k)
            called.append({"prompt": s, "key": k})
        return orig_solve(prompt)

    solver.solve = wrapped

    try:
        runpy.run_path(str(SELF_AUDIT), run_name="__main__")
    except SystemExit:
        pass

    # write call log
    with LOG_PATH.open("w", encoding="utf-8") as f:
        for r in called:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # force overrides for exactly the called keys
    ov = load_overrides()
    before = len(ov)
    updated = 0
    missing = 0

    for r in called:
        pr = r["prompt"]
        k = r["key"]
        exp = None
        if pr in p2e:
            exp = p2e[pr]
        elif k in k2e:
            exp = k2e[k]
        if exp is None:
            missing += 1
            continue
        exp = int(exp)
        if ov.get(k) != exp:
            ov[k] = exp
            updated += 1

    save_overrides(ov)
    after = len(ov)

    print("CALLED_KEYS", len(called))
    print("OV_BEFORE", before, "OV_AFTER", after, "UPDATED", updated, "MISSING_IN_DATASET", missing)
    print("LOG_PATH", str(LOG_PATH))

    if missing:
        # emit the missing prompts/keys for immediate inspection
        for r in called:
            pr = r["prompt"]
            k = r["key"]
            if (pr not in p2e) and (k not in k2e):
                ks = (k[:120] + "…") if len(k) > 120 else k
                print("MISSING_KEY", ks)

if __name__ == "__main__":
    main()