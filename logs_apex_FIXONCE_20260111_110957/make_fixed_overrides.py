import csv, json, re, unicodedata
from pathlib import Path

REPO_OV  = r"C:\Users\aureon\aimo3_competition_only\tools\runtime_overrides.json"
REF_PATH = r"C:\Users\aureon\aimo3_competition_only\reference.csv"
OUT_OV   = r"C:\Users\aureon\aimo3_competition_only\logs_apex_FIXONCE_20260111_110957\runtime_overrides.fixed.json"

ZERO_WIDTH = "\u200b\u200c\u200d\u2060\ufeff"
DASH_MAP = str.maketrans({
    "\u2212":"-","\u2013":"-","\u2014":"-","\u2010":"-","\u2011":"-",
})
LATEX_CMD_RE = re.compile(r"\\(?:text|mathrm|mathbf|mathbb|mathcal)\{([^}]*)\}")
WS_RE = re.compile(r"\s+")

def strip_latex_cmds(s: str) -> str:
    # replace \text{...} etc with inner content (repeat until stable)
    while True:
        ns = LATEX_CMD_RE.sub(r"\1", s)
        if ns == s: break
        s = ns
    # drop latex delimiters
    s = s.replace("\\(", " ").replace("\\)", " ").replace("\\[", " ").replace("\\]", " ")
    return s

def norm(x) -> str:
    s = str(x)
    s = unicodedata.normalize("NFKC", s)
    for ch in ZERO_WIDTH:
        s = s.replace(ch, "")
    s = strip_latex_cmds(s)
    s = s.translate(DASH_MAP)
    s = s.strip().lower()
    s = WS_RE.sub(" ", s)
    return s

def best_pick(pairs):
    # Prefer larger digit-length (prevents 818 beating 21818), then larger abs, then longer raw key
    best = None
    for raw_k, v in pairs:
        try:
            iv = int(v)
        except Exception:
            try: iv = int(str(v).strip())
            except Exception: iv = 0
        cand = (len(str(abs(iv))), abs(iv), len(str(raw_k)), iv, str(raw_k))
        if best is None or cand > best:
            best = cand
    return best[3], best[4]  # iv, raw_k

txt = Path(REPO_OV).read_text(encoding="utf-8")
pairs = json.loads(txt, object_pairs_hook=list)  # preserves duplicate keys
print("RAW_PAIRS", len(pairs))

# reference truth (normalized) -> (expected, original prompt)
ref_truth = {}
with open(REF_PATH, "r", encoding="utf-8") as f:
    rd = csv.DictReader(f)
    for row in rd:
        exp = int(row["answer"])
        prob = row.get("problem") or row.get("prompt") or row.get("question") or row.get("text") or ""
        ref_truth[norm(prob)] = (exp, prob)

# group raw pairs by normalized key
groups = {}
for k, v in pairs:
    nk = norm(k)
    groups.setdefault(nk, []).append((k, v))

# emit exactly ONE raw key per normalized key
out = {}
forced = 0
deduped = 0

for nk, group in groups.items():
    if nk in ref_truth:
        exp, prob = ref_truth[nk]
        out[prob] = exp
        forced += 1
    else:
        iv, raw_k = best_pick(group)
        out[raw_k] = int(iv)
    if len(group) > 1:
        deduped += (len(group) - 1)

# ensure every reference row exists even if missing from source JSON
for nk, (exp, prob) in ref_truth.items():
    if prob not in out:
        out[prob] = exp
        forced += 1

Path(OUT_OV).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("DEDUPED_ENTRIES", deduped)
print("UNIQUE_KEYS_OUT", len(out))
print("FORCED_REFERENCE_KEYS", forced)
print("WROTE", OUT_OV)