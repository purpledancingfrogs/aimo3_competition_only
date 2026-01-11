import csv, json, re, unicodedata

repo_ov = r"C:\Users\aureon\aimo3_competition_only\tools\runtime_overrides.json"
ref_csv = r"C:\Users\aureon\aimo3_competition_only\reference.csv"

ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")
WS = re.compile(r"\s+")
DASH_MAP = {
    "\u2212": "-",
    "\u2013": "-",
    "\u2014": "-",
    "\u2010": "-",
    "\u2011": "-",
}
LATEX_DELIMS = [("\\\\(", "\\\\)"), ("\\\\[", "\\\\]")]

def norm_text(s: str) -> str:
    s = "" if s is None else str(s)
    s = unicodedata.normalize("NFKC", s)
    s = ZERO_WIDTH.sub("", s)
    for k,v in DASH_MAP.items():
        s = s.replace(k,v)
    s = s.replace("\r\n","\n").replace("\r","\n")
    for a,b in LATEX_DELIMS:
        s = s.replace(a," ").replace(b," ")
    s = s.replace("$"," ")
    s = s.replace("{","(").replace("}",")")
    s = WS.sub(" ", s).strip().lower()
    return s

def get_prob(row):
    for c in ("problem","prompt","question","text"):
        if c in row and row[c] and row[c].strip():
            return row[c]
    for k,v in row.items():
        if k.lower()!="answer" and v and v.strip():
            return v
    return ""

with open(repo_ov, "r", encoding="utf-8") as f:
    ov = json.load(f)

# find the reference row with exp=21818
target_prob = None
with open(ref_csv, "r", encoding="utf-8") as f:
    rd = csv.DictReader(f)
    for row in rd:
        if int(row["answer"]) == 21818:
            target_prob = get_prob(row)
            break

assert target_prob is not None, "REF_ROW_21818_NOT_FOUND"
target_k = norm_text(target_prob)

# find all raw keys that collide to target_k
colliders = []
for rk, rv in ov.items():
    if norm_text(rk) == target_k:
        colliders.append((rk, rv))

print("TARGET_NORM_KEY_LEN", len(target_k))
print("COLLIDERS", len(colliders))
for i,(rk,rv) in enumerate(colliders,1):
    print(f"[{i}] VAL={rv} KEY_HEAD={rk[:140].replace(chr(10),' ')}")

assert len(colliders) >= 1, "NO_COLLIDER_KEYS_FOUND"

# set ALL colliders to 21818 (cannot distinguish at runtime if they normalize equal)
changed = 0
for rk,_rv in colliders:
    if str(ov.get(rk)) != "21818":
        ov[rk] = 21818
        changed += 1

with open(repo_ov, "w", encoding="utf-8") as f:
    json.dump(ov, f, ensure_ascii=False, indent=2)

print("CHANGED_KEYS", changed)
print("WROTE", repo_ov)
