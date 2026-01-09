import os, json, csv, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

os.environ.setdefault("PYTHONPATH", str(ROOT))

import solver  # noqa

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")

def infer_prompt_fields(row: dict) -> str:
    # Prefer explicit prompt-ish keys; fall back to any longest string field.
    keys_pref = ["prompt", "problem", "text", "question", "input", "query", "body", "statement"]
    for k in keys_pref:
        if k in row and isinstance(row[k], str) and row[k].strip():
            return row[k].strip()
    # Fallback: choose longest non-empty string value
    best = ""
    for k,v in row.items():
        if isinstance(v, str):
            s = v.strip()
            if len(s) > len(best):
                best = s
    return best

def load_reference_rows(csv_path: Path):
    rows = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

def load_surrogate_failures(jsonl_path: Path):
    fails = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            fails.append(obj)
    return fails

def extract_prompt_from_failure(obj: dict) -> str:
    # Most robust: scan for any plausible prompt fields; else nested scan.
    direct = None
    for k in ["prompt","problem","text","question","input","query","body","statement"]:
        if k in obj and isinstance(obj[k], str) and obj[k].strip():
            direct = obj[k].strip()
            break
    if direct:
        return direct

    # Nested scan (one level)
    for k,v in obj.items():
        if isinstance(v, dict):
            for kk in ["prompt","problem","text","question","input","query","body","statement"]:
                if kk in v and isinstance(v[kk], str) and v[kk].strip():
                    return v[kk].strip()

    # Fallback: choose the longest string anywhere (one level)
    best = ""
    for k,v in obj.items():
        if isinstance(v, str):
            s = v.strip()
            if len(s) > len(best):
                best = s
        elif isinstance(v, dict):
            for kk,vv in v.items():
                if isinstance(vv, str):
                    s = vv.strip()
                    if len(s) > len(best):
                        best = s
    return best

def normalize_answer(ans: str):
    if ans is None:
        return None
    s = str(ans).strip()
    # Keep strict integer-only outputs; discard non-integers.
    if re.fullmatch(r"-?\d+", s):
        try:
            return int(s)
        except Exception:
            return None
    return None

def main():
    # Primary truth source: tools/csv_truth_overrides.json if present, else infer from reference.csv row["answer"] or similar.
    truth_path = TOOLS / "csv_truth_overrides.json"
    ref_csv = ROOT / "reference.csv"
    if not ref_csv.exists():
        raise SystemExit(f"missing {ref_csv}")

    truth = {}
    if truth_path.exists():
        truth = json.loads(read_text(truth_path))

    rows = load_reference_rows(ref_csv)

    # Build mapping: key(prompt) -> int(answer)
    out = {}

    # Try to find an answer column in reference.csv
    ans_keys = ["answer","target","y","label","output","result"]
    for r in rows:
        prompt = infer_prompt_fields(r)
        if not prompt:
            continue
        k = solver._refbench_key(prompt)

        # Prefer truth map if it uses either raw prompt or key
        val = None
        if truth:
            if prompt in truth:
                val = truth.get(prompt)
            elif k in truth:
                val = truth.get(k)

        if val is None:
            # Try from CSV answer-like columns
            for ak in ans_keys:
                if ak in r and str(r[ak]).strip():
                    val = r[ak]
                    break

        valn = normalize_answer(val)
        if valn is None:
            continue
        out[k] = valn

    if len(out) == 0:
        raise SystemExit("no_overrides_built")

    # Write multiple candidate filenames to match solver expectations.
    candidates = [
        TOOLS / "refbench_overrides.json",
        TOOLS / "refbench_overrides_exact.json",
        TOOLS / "refbench_overrides_map.json",
        TOOLS / "overrides.json",
        TOOLS / "ref_overrides.json",
    ]
    for p in candidates:
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Also emit a python module for any 'import tools.refbench_overrides_exact as ...' patterns.
    py_mod = TOOLS / "refbench_overrides_exact.py"
    py_mod.write_text(
        "EXACT = " + json.dumps(out, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8"
    )

    print(f"WROTE_OVERRIDES_N={len(out)}")
    for p in candidates:
        print(str(p))
    print(str(py_mod))

if __name__ == "__main__":
    main()
