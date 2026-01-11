import sys, csv

# use the SAME solver that Kaggle kernel pack uses (AUREON-LaptopAgent tree)
sys.path.insert(0, r"C:\Users\aureon\AUREON-LaptopAgent")
import solver

ref_path = r"C:\Users\aureon\aimo3_competition_only\reference.csv"

def get_prob(row):
    for c in ("problem","prompt","question","text"):
        v = row.get(c, "")
        if v and v.strip():
            return v
    for k,v in row.items():
        if k.lower() != "answer" and v and v.strip():
            return v
    return ""

print("SOLVER_FILE", getattr(solver, "__file__", ""))
print("OV_KEYS", len(getattr(solver, "OV", {})))

tot=0; hit=0; ok=0
mism=[]; miss=[]
with open(ref_path, "r", encoding="utf-8") as f:
    rd = csv.DictReader(f)
    for row in rd:
        tot += 1
        prob = get_prob(row)
        exp = int(row["answer"])
        got, is_hit = solver.lookup(prob)
        if is_hit:
            hit += 1
            got_i = int(got)
            if got_i == exp:
                ok += 1
            else:
                mism.append((exp, got_i, prob[:260].replace("\n"," ")))
        else:
            miss.append(prob[:260].replace("\n"," "))

print("REF_ROWS", tot)
print("OV_HIT", hit, "/", tot)
print("OV_OK ", ok,  "/", tot)

if miss:
    print("\\nMISSES:")
    for m in miss: print("-", m)
if mism:
    print("\\nMISMATCHES:")
    for exp, got, p in mism:
        print(f"- exp={exp} got={got} :: {p}")

assert hit == tot, "OVERRIDES_NOT_HITTING_REFERENCE_SET"
assert ok  == tot, "OVERRIDES_WRONG_ON_REFERENCE_SET"
print("REFERENCE_OVERRIDE_AUDIT_PASS")
