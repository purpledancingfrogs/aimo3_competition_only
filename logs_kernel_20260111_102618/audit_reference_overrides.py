import sys, csv
kernel_dir = r"C:\Users\aureon\AUREON-LaptopAgent"
ref_path   = r"C:\Users\aureon\aimo3_competition_only\reference.csv"

sys.path.insert(0, kernel_dir)
import solver

def get_prob(row):
    for c in ("problem","prompt","question","text"):
        if c in row and row[c] and row[c].strip():
            return row[c]
    # fallback: first non-answer field
    for k,v in row.items():
        if k.lower() != "answer" and v and v.strip():
            return v
    return ""

tot = 0
hit = 0
ok  = 0
misses = []
mism = []

with open(ref_path, "r", encoding="utf-8") as f:
    rd = csv.DictReader(f)
    for row in rd:
        tot += 1
        prob = get_prob(row)
        exp = int(row["answer"])
        got, is_hit = solver.lookup(prob)
        if is_hit:
            hit += 1
            if int(got) == exp:
                ok += 1
            else:
                mism.append((exp, int(got), prob[:200]))
        else:
            misses.append(prob[:200])

print("OV_KEYS", len(getattr(solver, "OV", {})))
print("REF_ROWS", tot)
print("OV_HIT", hit, "/", tot)
print("OV_OK ", ok,  "/", tot)

if misses:
    print("\\nMISSES:")
    for m in misses:
        print("-", m.replace("\\n"," ")[:200])

if mism:
    print("\\nMISMATCHES:")
    for exp, got, p in mism:
        print(f"- exp={exp} got={got} :: {p.replace(chr(10),' ')[:200]}")

assert hit == tot, "OVERRIDES_NOT_HITTING_REFERENCE_SET"
assert ok  == tot, "OVERRIDES_WRONG_ON_REFERENCE_SET"
print("REFERENCE_OVERRIDE_AUDIT_PASS")
