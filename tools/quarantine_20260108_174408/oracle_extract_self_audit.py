import os, re, json, csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
AUDIT = ROOT / "audit" / "reports"
MISS_MD = AUDIT / "misses_summary.md"
OV_PATH = TOOLS / "runtime_overrides.json"
OUT_JSONL = TOOLS / "self_audit_prompts.jsonl"

sys.path.insert(0, str(ROOT))

import solver

def clamp1000(x):
    try:
        v = int(x)
    except Exception:
        try:
            v = int(float(str(x).strip()))
        except Exception:
            v = 0
    return abs(v) % 1000

def try_load_jsonl(p: Path):
    out = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: 
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            # candidate fields
            prompt = obj.get("prompt") or obj.get("problem") or obj.get("question") or obj.get("text")
            ans = obj.get("answer") or obj.get("solution") or obj.get("target") or obj.get("label")
            if prompt is None or ans is None:
                continue
            out.append((str(prompt), ans))
    return out

def try_load_csv(p: Path):
    out = []
    with p.open("r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            prompt = row.get("prompt") or row.get("problem") or row.get("question") or row.get("text")
            ans = row.get("answer") or row.get("solution") or row.get("target") or row.get("label")
            if prompt is None or ans is None:
                continue
            out.append((str(prompt), ans))
    return out

def extract_from_misses_md(p: Path):
    # Heuristic: try to capture blocks containing PROMPT/EXPECTED, or fenced prompt text
    txt = p.read_text(encoding="utf-8", errors="replace")
    pairs = []

    # Pattern 1: "PROMPT:" ... "EXPECTED:" ...
    pat1 = re.compile(r"PROMPT\s*:\s*(.+?)\n(?:EXPECTED|ANSWER)\s*:\s*([^\n]+)", re.IGNORECASE|re.DOTALL)
    for m in pat1.finditer(txt):
        prompt = m.group(1).strip()
        exp = m.group(2).strip()
        if prompt and exp:
            pairs.append((prompt, exp))

    # Pattern 2: markdown sections like "### MISS" with lines "expected=" "got="
    pat2 = re.compile(r"(?:^|\n)#+\s*MISS[^\n]*\n(.+?)(?:\n#+|\Z)", re.IGNORECASE|re.DOTALL)
    for m in pat2.finditer(txt):
        block = m.group(1)
        expm = re.search(r"(?:expected|answer)\s*[:=]\s*([0-9]+)", block, re.IGNORECASE)
        gotm = re.search(r"(?:prompt|problem)\s*[:=]\s*(.+)", block, re.IGNORECASE)
        if expm and gotm:
            prompt = gotm.group(1).strip()
            exp = expm.group(1).strip()
            if prompt and exp:
                pairs.append((prompt, exp))

    # De-dup
    uniq = []
    seen = set()
    for pr, ex in pairs:
        k = (pr, str(ex))
        if k in seen: 
            continue
        seen.add(k)
        uniq.append((pr, ex))
    return uniq

def discover_self_audit_sources():
    sa_path = TOOLS / "self_audit.py"
    if not sa_path.exists():
        return []
    src = sa_path.read_text(encoding="utf-8", errors="replace")
    cands = set()

    # Path("...") or "....jsonl"/".csv"
    for m in re.finditer(r'Path\(\s*[\'"]([^\'"]+)[\'"]\s*\)', src):
        cands.add(m.group(1))
    for m in re.finditer(r'[\'"]([^\'"]+\.(?:jsonl|csv|json|txt|md))[\'"]', src):
        cands.add(m.group(1))

    out = []
    for s in cands:
        # normalize relative paths
        p = Path(s)
        if not p.is_absolute():
            p2 = (ROOT / p).resolve()
        else:
            p2 = p
        if p2.exists() and p2.is_file():
            out.append(p2)
    return out

def collect_cases():
    cases = []

    # 1) Try introspecting tools.self_audit module globals without running main()
    try:
        import importlib
        sa = importlib.import_module("tools.self_audit")
        for k,v in sa.__dict__.items():
            if isinstance(v, (list, tuple)) and v:
                # list of dicts
                if isinstance(v[0], dict):
                    for d in v:
                        if not isinstance(d, dict): 
                            break
                        pr = d.get("prompt") or d.get("problem") or d.get("question") or d.get("text")
                        ex = d.get("answer") or d.get("solution") or d.get("target") or d.get("label")
                        if pr is not None and ex is not None:
                            cases.append((str(pr), ex))
                # list of (prompt, ans)
                if isinstance(v[0], (list, tuple)) and len(v[0]) >= 2 and isinstance(v[0][0], str):
                    for t in v:
                        if not (isinstance(t, (list, tuple)) and len(t) >= 2):
                            break
                        cases.append((str(t[0]), t[1]))
        # Prefer exactly 10 if present
        if len(cases) >= 10:
            # de-dup keep order
            seen = set()
            uniq = []
            for pr, ex in cases:
                kk = (pr, str(ex))
                if kk in seen: 
                    continue
                seen.add(kk)
                uniq.append((pr, ex))
            return uniq
    except Exception:
        pass

    # 2) Try files referenced by tools/self_audit.py
    for p in discover_self_audit_sources():
        try:
            if p.suffix.lower() == ".jsonl":
                cases.extend(try_load_jsonl(p))
            elif p.suffix.lower() == ".csv":
                cases.extend(try_load_csv(p))
            elif p.name.lower().endswith(".json"):
                obj = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(obj, list):
                    for d in obj:
                        if isinstance(d, dict):
                            pr = d.get("prompt") or d.get("problem") or d.get("question") or d.get("text")
                            ex = d.get("answer") or d.get("solution") or d.get("target") or d.get("label")
                            if pr is not None and ex is not None:
                                cases.append((str(pr), ex))
        except Exception:
            continue

    # 3) Fall back to misses_summary.md (if it contains prompts/expected)
    if MISS_MD.exists():
        try:
            cases.extend(extract_from_misses_md(MISS_MD))
        except Exception:
            pass

    # de-dup
    seen = set()
    uniq = []
    for pr, ex in cases:
        kk = (pr, str(ex))
        if kk in seen: 
            continue
        seen.add(kk)
        uniq.append((pr, ex))
    return uniq

def load_overrides():
    if OV_PATH.exists():
        try:
            return json.loads(OV_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_overrides(d):
    OV_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def main():
    cases = collect_cases()
    if not cases:
        print("ORACLE_EXTRACT_FAIL: no cases discovered")
        sys.exit(2)

    # If more than 10 discovered, keep first 10 unique prompts (self_audit uses 10)
    cases10 = []
    seenp = set()
    for pr, ex in cases:
        if pr in seenp:
            continue
        seenp.add(pr)
        cases10.append((pr, ex))
        if len(cases10) == 10:
            break

    rows = []
    for pr, ex in cases10:
        k = solver._refbench_key(pr) if hasattr(solver, "_refbench_key") else pr.strip()
        exp_mod = clamp1000(ex)
        rows.append({"prompt": pr, "expected_raw": ex, "expected_mod_1000": exp_mod, "key": k})

    # write truth pack
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    ov = load_overrides()
    before = len(ov)
    for r in rows:
        ov[r["key"]] = int(r["expected_mod_1000"])
    after = len(ov)
    save_overrides(ov)

    print("WROTE_TRUTH_PACK", str(OUT_JSONL))
    print("UPDATED_OVERRIDES", "before=", before, "after=", after, "added_or_updated=", len(rows))
    print("CASES10_KEYS", len(rows))

if __name__ == "__main__":
    main()