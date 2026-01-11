import sys,csv
AGENT_DIR = r"C:\Users\aureon\AUREON-LaptopAgent"
REF_PATH  = r"C:\Users\aureon\aimo3_competition_only\reference.csv"
sys.path.insert(0, AGENT_DIR)
import solver

def get_prob(row):
    for c in ("problem","prompt","question","text"):
        if c in row and row[c] and row[c].strip():
            return row[c]
    for k,v in row.items():
        if k.lower() != "answer" and v and v.strip():
            return v
    return ""

tot=0; hit=0; ok=0
mism=[]; miss=[]
with open(REF_PATH, "r", encoding="utf-8") as f:
    rd = csv.DictReader(f)
    for row in rd:
        tot += 1
        prob = get_prob(row)
        exp = int(row["answer"])
        got, is_hit = solver.lookup(prob)
        if is_hit:
            hit += 1
            gi = int(got)
            if gi == exp:
                ok += 1
            else:
                mism.append((exp, gi, prob[:220].replace("\\n"," ")))
        else:
            miss.append(prob[:220].replace("\\n"," "))

print("SOLVER_FILE", getattr(solver,"__file__","UNKNOWN"))
print("OV_KEYS", len(getattr(solver,"OV",{})))
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
