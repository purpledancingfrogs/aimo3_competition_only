from __future__ import annotations
import csv, json, re, subprocess, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

ID_CANDS   = ["id","problem_id","uid"]
TEXT_CANDS = ["problem","question","text","prompt","statement"]
ANS_CANDS  = ["answer","output","target","label","gold"]

def _pick(hdr, cands):
    m = {k.lower(): k for k in (hdr or [])}
    for c in cands:
        if c.lower() in m:
            return m[c.lower()]
    return None

def _read_csv(p: Path):
    with p.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        hdr = r.fieldnames or []
        rows = list(r)
    return hdr, rows

def _parse_intish(x):
    if x is None:
        return None
    s = str(x).strip()
    if s == "":
        return None
    s = s.replace(",", "").replace(" ", "")
    m = re.findall(r"-?\d+", s)
    return int(m[-1]) if m else None

def load_dataset():
    prob_paths = [ROOT/"problems.csv", ROOT/"kaggle_data"/"problems.csv"]
    ref_paths  = [ROOT/"reference.csv", ROOT/"kaggle_data"/"reference.csv"]

    prob_p = next((p for p in prob_paths if p.exists()), None)
    ref_p  = next((p for p in ref_paths if p.exists()), None)

    prob_hdr = prob_rows = None
    ref_hdr  = ref_rows  = None

    if prob_p:
        prob_hdr, prob_rows = _read_csv(prob_p)
    if ref_p:
        ref_hdr, ref_rows = _read_csv(ref_p)

    mode = "NONE"

    # Column detection
    pid = _pick(prob_hdr, ID_CANDS) if prob_hdr else None
    ptxt = _pick(prob_hdr, TEXT_CANDS) if prob_hdr else None
    pans = _pick(prob_hdr, ANS_CANDS) if prob_hdr else None

    rid = _pick(ref_hdr, ID_CANDS) if ref_hdr else None
    rtxt = _pick(ref_hdr, TEXT_CANDS) if ref_hdr else None
    rans = _pick(ref_hdr, ANS_CANDS) if ref_hdr else None

    # Prefer join when ids intersect
    dataset = []
    if prob_rows and ref_rows and pid and ptxt and rid and rans:
        rmap = {}
        for rr in ref_rows:
            k = (rr.get(rid, "") or "").strip()
            if k != "":
                rmap[k] = rr
        inter = 0
        for pr in prob_rows:
            k = (pr.get(pid, "") or "").strip()
            if k in rmap:
                inter += 1
        if inter > 0:
            mode = f"JOIN(problems<->reference) inter={inter}"
            for pr in prob_rows:
                k = (pr.get(pid, "") or "").strip()
                if k in rmap:
                    gold = rmap[k].get(rans, None)
                    dataset.append((k, pr.get(ptxt, ""), gold))
            return mode, prob_p, ref_p, dataset

    # Fallback: use reference.csv as both problem+gold (most useful for real scoring)
    if ref_rows and rid and rtxt and rans:
        mode = "REFERENCE_AS_DATASET(reference.csv has problem+answer)"
        for rr in ref_rows:
            k = (rr.get(rid, "") or "").strip()
            dataset.append((k, rr.get(rtxt, ""), rr.get(rans, None)))
        return mode, prob_p, ref_p, dataset

    # Fallback: problems.csv has inline gold
    if prob_rows and pid and ptxt and pans:
        mode = "PROBLEMS_INLINE_GOLD(problems.csv has answer)"
        for pr in prob_rows:
            k = (pr.get(pid, "") or "").strip()
            dataset.append((k, pr.get(ptxt, ""), pr.get(pans, None)))
        return mode, prob_p, ref_p, dataset

    return mode, prob_p, ref_p, []

def load_solver_callable():
    try:
        import importlib
        solver = importlib.import_module("solver")
        if hasattr(solver, "solve") and callable(getattr(solver, "solve")):
            return ("import:solve(text)", lambda t: str(solver.solve(t)).strip())
        if hasattr(solver, "Solver"):
            S = solver.Solver
            if callable(S) and hasattr(S, "solve"):
                inst = S()
                return ("import:Solver().solve(text)", lambda t: str(inst.solve(t)).strip())
    except Exception:
        pass

    solver_py = ROOT / "solver.py"
    def run_subprocess(text: str) -> str:
        p = subprocess.run(
            [sys.executable, str(solver_py)],
            input=text,
            text=True,
            capture_output=True,
            cwd=str(ROOT),
            timeout=60,
        )
        out = (p.stdout or "").strip()
        if out == "" and p.stderr:
            out = (p.stderr or "").strip()
        return out
    return ("subprocess:python solver.py <stdin>", run_subprocess)

def main():
    mode, prob_p, ref_p, data = load_dataset()
    solver_mode, solve_fn = load_solver_callable()

    out_dir = ROOT / "audit" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_md = out_dir / "misses_summary.md"
    out_jsonl = out_dir / "misses.jsonl"

    total = 0
    correct = 0
    misses = []

    for k, q, g_raw in data:
        q = "" if q is None else str(q)
        g = _parse_intish(g_raw)
        if g is None:
            continue
        total += 1
        try:
            pred_raw = solve_fn(q)
        except Exception as e:
            pred_raw = f"ERR:{type(e).__name__}:{e}"
        p = _parse_intish(pred_raw)
        ok = (p == g)
        if ok:
            correct += 1
        else:
            snip = " ".join(q.split())[:180]
            misses.append({"id": k, "gold": g, "pred": p, "pred_raw": str(pred_raw)[:2000], "snippet": snip})

    acc = (correct / total) if total else 0.0

    with out_jsonl.open("w", encoding="utf-8") as f:
        for m in misses:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    with out_md.open("w", encoding="utf-8") as f:
        f.write(f"generated_at={datetime.utcnow().isoformat()}Z\n")
        f.write(f"mode={mode}\n")
        f.write(f"solver_mode={solver_mode}\n")
        f.write(f"problems_path={prob_p}\n")
        f.write(f"reference_path={ref_p}\n")
        f.write(f"TOTAL={total} CORRECT={correct} ACC={acc:.4f} MISSES={len(misses)}\n\n")
        f.write("Top 50 misses:\n")
        for i, m in enumerate(misses[:50], 1):
            f.write(f"{i:02d}. id={m['id']} gold={m['gold']} pred={m['pred']} :: {m['snippet']}\n")

    print(str(out_md))
    print(f"TOTAL={total} CORRECT={correct} ACC={acc:.4f} MISSES={len(misses)}")
    if total == 0:
        print("NOTE: still no usable gold labels detected (dataset mismatch or missing answer column).", file=sys.stderr)

if __name__ == "__main__":
    main()