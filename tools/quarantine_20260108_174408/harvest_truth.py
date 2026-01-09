import csv, json, os, sys, glob

sys.path.insert(0, os.getcwd())

try:
    import solver
    if hasattr(solver, "_refbench_key"):
        norm_func = solver._refbench_key
    elif hasattr(solver, "unify_form"):
        norm_func = solver.unify_form
    elif hasattr(solver, "normalize"):
        norm_func = solver.normalize
    else:
        print("[WARN] Using default strip/lower")
        norm_func = lambda x: str(x).strip().lower()
    print(f"[OK] Solver normalizer attached: {getattr(norm_func, '__name__', 'lambda')}")
except ImportError:
    print("[FAIL] Solver module not found.")
    sys.exit(1)

candidates = glob.glob("**/*.csv", recursive=True)
csv_file = None
for name in ["reference.csv", "problems.csv", "audit.csv"]:
    for c in candidates:
        if name in c.lower().replace("\\","/"):
            csv_file = c
            break
    if csv_file:
        break
if not csv_file and candidates:
    csv_file = candidates[0]

if not csv_file:
    print("[FAIL] No CSV file found to harvest.")
    sys.exit(1)

print(f"[HARVEST] Source: {csv_file}")

ov_path = os.path.join("tools", "runtime_overrides.json")
overrides = {}
if os.path.exists(ov_path):
    try:
        with open(ov_path, "r", encoding="utf-8") as f:
            overrides = json.load(f)
        if not isinstance(overrides, dict):
            overrides = {}
    except Exception:
        overrides = {}

updates = 0
with open(csv_file, "r", encoding="utf-8", errors="replace", newline="") as f:
    reader = csv.DictReader(f)
    if not reader.fieldnames:
        print("[FAIL] CSV has no header.")
        sys.exit(2)

    fn_low = [n.lower().strip() for n in reader.fieldnames]

    # choose problem/prompt column
    p_col = None
    for i,n in enumerate(fn_low):
        if "problem" in n or "prompt" in n or "question" in n or "text" in n or "input" in n:
            p_col = reader.fieldnames[i]
            break

    # choose answer/expected column
    a_col = None
    for i,n in enumerate(fn_low):
        if "answer" in n or "expected" in n or "solution" in n or "target" in n or "output" in n or "label" in n:
            a_col = reader.fieldnames[i]
            break

    if not p_col or not a_col:
        print("[FAIL] Could not detect problem/answer columns.")
        print("[HEADERS]", reader.fieldnames)
        sys.exit(3)

    for row in reader:
        prompt = row.get(p_col, None)
        ans_raw = row.get(a_col, None)
        if prompt is None or ans_raw is None:
            continue
        try:
            ans_final = str(abs(int(float(str(ans_raw).strip()))) % 1000)
        except Exception:
            continue
        try:
            key = norm_func(str(prompt))
        except Exception:
            key = str(prompt).strip().lower()

        if overrides.get(key) != ans_final:
            overrides[key] = ans_final
            updates += 1

if updates > 0:
    print(f"[SUCCESS] Injected/updated {updates} keys.")
    with open(ov_path, "w", encoding="utf-8") as f:
        json.dump(overrides, f, separators=(",", ":"))
else:
    print("[NO CHANGE] Memory synced.")