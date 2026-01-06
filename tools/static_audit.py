import ast, re, sys, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOLVER = ROOT/"solver.py"
REQ = ROOT/"requirements.txt"

BAD_PATTERNS = [
  r"\brandom\.", r"\bos\.urandom\b", r"\btime\.time\b", r"\bdatetime\.now\b", r"\bperf_counter\b",
  r"\brequests\b", r"\burllib\b", r"\bsocket\b"
]

def read(p): return p.read_text(encoding="utf-8", errors="replace")

def find_bad(text):
  hits=[]
  for pat in BAD_PATTERNS:
    if re.search(pat, text):
      hits.append(pat)
  return hits

def imports_in_file(text):
  imps=set()
  try:
    tree=ast.parse(text)
    for n in ast.walk(tree):
      if isinstance(n, ast.Import):
        for a in n.names: imps.add(a.name.split(".")[0])
      elif isinstance(n, ast.ImportFrom):
        if n.module: imps.add(n.module.split(".")[0])
  except Exception:
    pass
  return sorted(imps)

def req_pkgs():
  if not REQ.exists(): return set()
  pk=set()
  for line in read(REQ).splitlines():
    line=line.strip()
    if not line or line.startswith("#"): continue
    name=re.split(r"[<=> ]", line, 1)[0].strip()
    if name: pk.add(name.lower())
  return pk

def find_prints(text):
  # allow prints only under if __name__ == "__main__" guard (best-effort heuristic)
  lines=text.splitlines()
  bad=[]
  for i,l in enumerate(lines,1):
    if re.search(r"(^|\s)print\s*\(", l):
      bad.append(i)
  return bad

def main():
  s=read(SOLVER)
  rep={}
  rep["solver_exists"]=SOLVER.exists()
  rep["bad_patterns"]=find_bad(s)
  rep["imports"]=imports_in_file(s)
  rep["print_lines"]=find_prints(s)
  req=req_pkgs()
  rep["requirements_exists"]=REQ.exists()
  rep["requirements"]=sorted(req)

  # dependency sanity: if solver imports sympy/numpy/polars, ensure pinned/declared
  needs=[]
  for pkg in ["sympy","numpy","polars"]:
    if pkg in [x.lower() for x in rep["imports"]] and pkg not in req:
      needs.append(pkg)
  rep["missing_requirements"]=needs

  ok = (len(rep["bad_patterns"])==0) and (len(rep["missing_requirements"])==0)
  rep["audit_ok"]=ok

  out=ROOT/"tools"/"static_audit_report.json"
  out.parent.mkdir(parents=True, exist_ok=True)
  out.write_text(json.dumps(rep, indent=2, sort_keys=True), encoding="utf-8")
  print(out.as_posix())
  print(json.dumps(rep, indent=2, sort_keys=True))
  if not ok:
    sys.exit(2)

if __name__=="__main__":
  main()
