import re, importlib, inspect, pathlib, sys

p = pathlib.Path("solver.py")
s = p.read_text(encoding="utf-8", errors="ignore")

print("solver.py bytes:", len(s))
print("Top defs (first 80):")
for m in re.finditer(r"(?m)^(\s*)def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", s):
    print("DEF", repr(m.group(1)), m.group(2))
print("Top classes:")
for m in re.finditer(r"(?m)^class\s+([A-Za-z_][A-Za-z0-9_]*)\b", s):
    print("CLASS", m.group(1))

print("\n--- inference_server: key lines ---")
inf = pathlib.Path("kaggle_evaluation/aimo_3_inference_server.py").read_text(encoding="utf-8", errors="ignore")
for pat in ["import solver","from solver","def predict","def inference","def solve","Solver","MODEL","run","stdin","json"]:
    if pat in inf:
        print("HAS", pat)
print("inference_server defs:")
for m in re.finditer(r"(?m)^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", inf):
    print("DEF", m.group(1))

print("\n--- try import solver ---")
try:
    mod = importlib.import_module("solver")
    cand = [n for n in dir(mod) if any(k in n.lower() for k in ["solve","predict","infer","answer","run"])]
    print("solver module candidates:", cand)
except Exception as e:
    print("IMPORT_SOLVER_FAILED:", type(e).__name__, str(e))

print("\n--- try import inference_server ---")
try:
    ims = importlib.import_module("kaggle_evaluation.aimo_3_inference_server")
    cand = [n for n in dir(ims) if any(k in n.lower() for k in ["solve","predict","infer","answer","run"])]
    print("inference_server candidates:", cand)
except Exception as e:
    print("IMPORT_INFERENCE_SERVER_FAILED:", type(e).__name__, str(e))
