import json, re, unicodedata, hashlib
from pathlib import Path
p = Path(r"C:\Users\aureon\aimo3_competition_only\tools\runtime_overrides_kaggle.json")
raw = p.read_bytes()
sha = hashlib.sha256(raw).hexdigest().upper()
txt = raw.decode("utf-8-sig")
obj = json.loads(txt)
raw_keys = list(obj.keys())
def keyfn(s: str) -> str:
    s = str(s).replace("\ufeff","")
    s = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff]", "", s)
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(str.maketrans({"–":"-","—":"-","−":"-"}))
    s = re.sub(r"\s+", " ", s).strip()
    return s.casefold()
norm_map = {}
collisions = {}
for k in raw_keys:
    nk = keyfn(k)
    if nk in norm_map and norm_map[nk] != k:
        collisions.setdefault(nk, set()).update([norm_map[nk], k])
    else:
        norm_map[nk] = k
print("SHA256", sha)
print("RAW_KEYS", len(raw_keys))
print("NORM_KEYS", len(norm_map))
print("COLLISIONS", len(collisions))
if len(raw_keys) != 64: raise SystemExit("BAD_KEYCOUNT_RAW")
if len(norm_map) != 64: raise SystemExit("BAD_KEYCOUNT_NORM")
if len(collisions) != 0: raise SystemExit("BAD_COLLISIONS")
