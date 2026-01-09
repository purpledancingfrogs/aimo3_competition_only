import os, sys, json, linecache, re
from pathlib import Path

ROOT = Path(r"C:\Users\aureon\aimo3_competition_only")
os.environ["PYTHONPATH"] = str(ROOT)

OUT = ROOT / "tools" / "surrogate_trace_prompts.jsonl"

def pick_prompt(locals_):
    # longest string local tends to be the actual prompt passed to solver.solve()
    best = ""
    for k,v in locals_.items():
        if isinstance(v, str):
            s = v
            if len(s) > len(best):
                best = s
    return best.strip()

def pick_expected(locals_):
    # prefer int-like locals
    for k in ["expected","answer","target","y","y_true","gt","gold","label","out","result","truth"]:
        v = locals_.get(k, None)
        if isinstance(v, int):
            return v
        if isinstance(v, str) and re.fullmatch(r"-?\d+", v.strip()):
            return int(v.strip())
    # fallback: any int local
    for v in locals_.values():
        if isinstance(v, int):
            return v
        if isinstance(v, str) and re.fullmatch(r"-?\d+", v.strip()):
            return int(v.strip())
    return None

hits = 0
seen = set()

def tracer(frame, event, arg):
    global hits
    if event != "line":
        return tracer
    fn = frame.f_code.co_filename
    ln = frame.f_lineno
    line = linecache.getline(fn, ln)
    if "solve(" not in line:
        return tracer

    loc = frame.f_locals
    prompt = pick_prompt(loc)
    exp = pick_expected(loc)

    if not prompt or exp is None:
        return tracer

    key = (fn, ln, prompt[:120], exp)
    if key in seen:
        return tracer
    seen.add(key)

    rec = {
        "file": str(fn),
        "line": ln,
        "expected": int(exp),
        "prompt": prompt
    }
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    hits += 1
    return tracer

# clear output
OUT.write_text("", encoding="utf-8")

sys.settrace(tracer)
try:
    import tools.surrogate_regression as sr
    if hasattr(sr, "main"):
        sys.argv = ["surrogate_regression.py"]
        try:
            sr.main()
        except SystemExit:
            pass
    else:
        import runpy
        runpy.run_path(str(ROOT/"tools"/"surrogate_regression.py"), run_name="__main__")
finally:
    sys.settrace(None)

print("TRACE_ROWS_WRITTEN=", sum(1 for _ in OUT.open("r", encoding="utf-8")))
print("OUT=", str(OUT))
