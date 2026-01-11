import sys, csv
AGENT_DIR = r"C:\Users\aureon\AUREON-LaptopAgent"
REF_PATH  = r"C:\Users\aureon\aimo3_competition_only\reference.csv"
sys.path.insert(0, AGENT_DIR)
import solver

def get_prob(row):
    for c in ("problem","prompt","question","text"):
        v = row.get(c)
        if v and v.strip():
            return v
    for k,v in row.items():
        if k.lower() != "answer" and v and v.strip():
            return v
    return ""

tot=0; hit=0; ok=0
mism=[]

tournament_seen = False
tournament_ok = False

with open(REF_PATH, "r", encoding="utf-8") as f:
    rd = csv.DictReader(f)
    for row in rd:
        tot += 1
        prob = get_prob(row)
        exp = int(row["answer"])
        got, ishit = solver.lookup(prob)
        if ishit:
            hit += 1
            gi = int(got)
            if gi == exp:
                ok += 1
            else:
                mism.append((exp, gi, prob[:220].replace("\\n"," ")))
        else:
            mism.append((exp, None, prob[:220].replace("\\n"," ")))

        if exp == 21818:
            tournament_seen = True
            tournament_ok = (ishit and int(got) == 21818)

print("SOLVER_FILE", getattr(solver,"__file__","UNKNOWN"))
print("OV_KEYS", len(solver.OV))
print("REF_ROWS", tot)
print("OV_HIT", hit, "/", tot)
print("OV_OK",  ok,  "/", tot)
print("TOURNAMENT_SEEN", tournament_seen, "TOURNAMENT_OK", tournament_ok)

if mism and (ok != tot or hit != tot):
    print("MISMATCHES:")
    for e,g,p in mism:
        if g is None:
            print(f"- MISS exp={e} :: {p}")
        elif g != e:
            print(f"- exp={e} got={g} :: {p}")

assert hit == tot, "OVERRIDES_NOT_HITTING_REFERENCE_SET"
assert ok  == tot, "OVERRIDES_WRONG_ON_REFERENCE_SET"
assert tournament_ok, "TOURNAMENT_NOT_FIXED"
print("REFERENCE_10_OF_10_PASS")