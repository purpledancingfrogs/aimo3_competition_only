import os, csv, json, glob, traceback
import solver

TEXT_KEYS = ["text","prompt","problem","question","input","statement"]
ANS_KEYS  = ["expected","answer","output","solution","label","target"]

def pick(d, keys):
    for k in keys:
        if k in d and d[k] not in (None,""):
            return d[k]
    return None

def norm_ans(x):
    if x is None: return None
    if isinstance(x,(int,float)): return str(int(x)) if float(x).is_integer() else str(x)
    s = str(x).strip()
    s = s.replace("\u00a0"," ").strip()
    return s

def iter_csv(path):
    with open(path,"r",encoding="utf-8-sig",newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except Exception:
            dialect = csv.excel
        r = csv.DictReader(f, dialect=dialect)
        for row in r:
            yield row

def iter_jsonl(path):
    with open(path,"r",encoding="utf-8-sig") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try:
                yield json.loads(line)
            except Exception:
                continue

def eval_items(items, src):
    tot=ok=0
    fails=[]
    for d in items:
        txt = pick(d,TEXT_KEYS)
        exp = pick(d,ANS_KEYS)
        if txt is None or exp is None: 
            continue
        exp = norm_ans(exp)
        if exp is None: 
            continue
        tot += 1
        try:
            got_raw = solver.solve(txt)
            got = norm_ans(got_raw)
        except Exception as e:
            got_raw = f"EXC:{type(e).__name__}:{e}"
            got = None
        if got == exp:
            ok += 1
        else:
            fails.append({
                "src": src,
                "expected": exp,
                "got": got,
                "got_raw": got_raw,
                "text_head": txt[:280].replace("\n"," ")})
    return tot, ok, fails

paths = []
for pat in ["**/*.csv","**/*.jsonl"]:
    paths += glob.glob(pat, recursive=True)

# skip huge or irrelevant dirs
SKIP = set([".git\\","__pycache__\\",".venv\\","venv\\","site-packages\\","dist\\","build\\"])
def skip(p):
    lp = p.lower().replace("/","\\")
    return any(s in lp for s in SKIP)

paths = [p for p in paths if not skip(p)]
paths.sort(key=lambda x: (x.count(os.sep), x))

all_fails=[]
sum_rows=[]

for p in paths:
    try:
        if p.lower().endswith(".csv"):
            tot, ok, fails = eval_items(iter_csv(p), p)
        else:
            tot, ok, fails = eval_items(iter_jsonl(p), p)
        if tot>0:
            sum_rows.append((p, tot, ok, ok/tot))
            all_fails.extend(fails)
    except Exception:
        continue

os.makedirs("tools", exist_ok=True)
with open("tools/widebench_summary.txt","w",encoding="utf-8") as f:
    for p,tot,ok,acc in sorted(sum_rows, key=lambda t: (-t[3], -t[2], t[0])):
        f.write(f"{p}\tN={tot}\tOK={ok}\tACC={acc:.6f}\n")
with open("tools/widebench_failures.jsonl","w",encoding="utf-8") as f:
    for r in all_fails:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("FILES_EVAL=", len(sum_rows))
print("TOTAL_N=", sum(t for _,t,_,_ in sum_rows))
print("TOTAL_OK=", sum(o for _,_,o,_ in sum_rows))
print("WROTE tools/widebench_summary.txt")
print("WROTE tools/widebench_failures.jsonl")
