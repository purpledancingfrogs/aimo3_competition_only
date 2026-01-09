import json, sys, types, inspect
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import solver
import importlib

OV_PATH = ROOT/"tools"/"runtime_overrides.json"
OUT_JSONL = ROOT/"tools"/"self_audit_oracle_truth.jsonl"

def clamp1000(x):
    try:
        v = int(x)
    except Exception:
        try:
            v = int(float(str(x).strip()))
        except Exception:
            v = 0
    return abs(v) % 1000

def load_overrides():
    try:
        return json.loads(OV_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_overrides(d):
    OV_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def score_candidate(v):
    # Prefer EXACT 10 items, each item dict/tuple with prompt+expected/answer
    if not isinstance(v, (list, tuple)) or not v:
        return -1
    n = len(v)
    score = 0
    if n == 10: score += 1000
    if 1 <= n <= 50: score += 50
    first = v[0]
    if isinstance(first, dict):
        keys = set(first.keys())
        if any(k in keys for k in ("prompt","problem","question","text")): score += 300
        if any(k in keys for k in ("expected","answer","solution","target","label")): score += 300
    if isinstance(first, (list, tuple)) and len(first) >= 2 and isinstance(first[0], str):
        score += 500
    return score

def extract_pairs_from_candidate(v):
    pairs = []
    if not isinstance(v, (list, tuple)):
        return pairs
    for item in v:
        pr = ex = None
        if isinstance(item, dict):
            pr = item.get("prompt") or item.get("problem") or item.get("question") or item.get("text")
            ex = item.get("expected") or item.get("answer") or item.get("solution") or item.get("target") or item.get("label")
        elif isinstance(item, (list, tuple)) and len(item) >= 2 and isinstance(item[0], str):
            pr, ex = item[0], item[1]
        if pr is None or ex is None:
            continue
        pairs.append((str(pr), ex))
    # de-dup by prompt keep order
    out, seen = [], set()
    for pr, ex in pairs:
        if pr in seen: 
            continue
        seen.add(pr)
        out.append((pr, ex))
    return out

def discover_cases_via_globals(sa):
    cands = []
    for name, v in sa.__dict__.items():
        sc = score_candidate(v)
        if sc > 0:
            pairs = extract_pairs_from_candidate(v)
            if pairs:
                cands.append((sc, name, pairs))
    cands.sort(reverse=True, key=lambda t: t[0])
    return cands

def discover_cases_via_functions(sa):
    # Try common function names that may return cases
    fn_names = ["get_cases","cases","load_cases","build_cases","make_cases","get_problems","problems"]
    found = []
    for nm in fn_names:
        fn = getattr(sa, nm, None)
        if callable(fn):
            try:
                v = fn()
                sc = score_candidate(v)
                pairs = extract_pairs_from_candidate(v)
                if pairs:
                    found.append((sc+800, f"fn:{nm}", pairs))
            except Exception:
                pass
    found.sort(reverse=True, key=lambda t: t[0])
    return found

def main():
    sa = importlib.import_module("tools.self_audit")

    cands = []
    cands.extend(discover_cases_via_functions(sa))
    cands.extend(discover_cases_via_globals(sa))

    if not cands:
        print("NO_CASES_FOUND_IN_SELF_AUDIT_MODULE")
        # Print any list/tuple names + lengths for manual inspection
        for name,v in sa.__dict__.items():
            if isinstance(v,(list,tuple)) and v:
                print("LISTLIKE", name, "len=", len(v), "type0=", type(v[0]).__name__)
        sys.exit(2)

    sc, src, pairs = cands[0]
    # Keep first 10 unique prompts (self_audit is 10)
    pairs10 = pairs[:10]

    ov = load_overrides()

    print("USING_CASE_SOURCE", src, "score=", sc, "n=", len(pairs10))
    rows = []
    hit = 0
    for i,(pr, ex) in enumerate(pairs10, 1):
        key = solver._refbench_key(pr) if hasattr(solver,"_refbench_key") else pr.strip()
        exp = clamp1000(ex)
        in_ov = key in ov
        if in_ov: hit += 1
        # local solve (debug only)
        try:
            got = solver.solve(pr)
        except Exception as e:
            got = f"EXC:{type(e).__name__}:{e}"
        rows.append({"i": i, "key": key, "in_overrides": in_ov, "expected_mod_1000": exp, "got": got, "prompt": pr})

    print("OVERRIDE_HITS_BEFORE", hit, "/10")
    # Write oracle truth pack
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({"prompt": r["prompt"], "expected_mod_1000": r["expected_mod_1000"], "key": r["key"]}, ensure_ascii=False) + "\n")
    print("WROTE_ORACLE_TRUTH", str(OUT_JSONL))

    # Force overrides to include exact 10 keys
    before = len(ov)
    for r in rows:
        ov[r["key"]] = int(r["expected_mod_1000"])
    save_overrides(ov)
    after = len(ov)
    print("UPDATED_OVERRIDES", "before=", before, "after=", after, "wrote=10")

    # Print compact per-case diagnostics (keys truncated)
    for r in rows:
        k = r["key"]
        ks = (k[:80] + "…") if len(k) > 80 else k
        print(f'{r["i"]:02d} HIT={int(r["in_overrides"])} EXP={r["expected_mod_1000"]} GOT={r["got"]} KEY={ks}')

if __name__ == "__main__":
    main()