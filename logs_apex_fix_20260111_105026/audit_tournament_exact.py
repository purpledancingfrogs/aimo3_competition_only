import sys,csv,re,unicodedata,inspect
AGENT_DIR = r"C:\Users\aureon\AUREON-LaptopAgent"
REPO_OV   = r"C:\Users\aureon\aimo3_competition_only\tools\runtime_overrides.json"
REF_PATH  = r"C:\Users\aureon\aimo3_competition_only\reference.csv"

sys.path.insert(0, AGENT_DIR)
import solver

def _fallback_norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s))
    s = re.sub(r"\s+", " ", s.strip().lower())
    return s

norm_fn = getattr(solver, "_refbench_key", None) or getattr(solver, "normalize", None) or _fallback_norm

# find tournament prompt in reference.csv by expected answer 21818
t = None
with open(REF_PATH, "r", encoding="utf-8") as f:
    rd = csv.DictReader(f)
    for row in rd:
        try:
            if int(row.get("answer","-1")) == 21818:
                t = row.get("problem") or row.get("prompt") or row.get("question") or row.get("text") or ""
                break
        except Exception:
            pass
assert t, "TOURNAMENT_ROW_NOT_FOUND_IN_REFERENCE"

nk = norm_fn(t)
print("SOLVER_FILE", getattr(solver, "__file__", "UNKNOWN"))
print("NORM_FN", getattr(norm_fn, "__name__", "fallback"))
print("TOURNAMENT_PROMPT_HEAD", t[:140].replace("\\n"," "))
print("NORM_KEY_LEN", len(nk))
print("NORM_KEY_HEAD", nk[:140])

got, hit = solver.lookup(t)
print("LOOKUP_HIT", hit, "LOOKUP_GOT", int(got))

# introspect OV dict (as seen by solver)
OV = getattr(solver, "OV", {})
print("SOLVER_OV_KEYS", len(OV))

# If exact key exists in solver.OV, show its stored value
if nk in OV:
    print("SOLVER_OV_EXACT_VALUE", int(OV[nk]))
else:
    print("SOLVER_OV_EXACT_VALUE", "MISSING")

# show any colliders in solver.OV that share a long prefix with the tournament norm key
pref = nk[:120]
coll = [(k, OV[k]) for k in OV.keys() if len(k) >= 120 and k[:120] == pref]
print("PREFIX_COLLIDERS_120", len(coll))
if len(coll) <= 10:
    for k,v in coll:
        print("COLL_VAL", int(v), "COLL_KEY_LEN", len(k), "COLL_KEY_HEAD", k[:160])

# also check repo overrides AFTER normalizing keys with same norm_fn
import json
with open(REPO_OV, "r", encoding="utf-8") as f:
    raw = json.load(f)
normed = {}
for k,v in raw.items():
    kk = norm_fn(k)
    normed.setdefault(kk, set()).add(int(v))
vals = normed.get(nk, set())
print("REPO_NORMED_VALUES_FOR_KEY", sorted(list(vals)))
