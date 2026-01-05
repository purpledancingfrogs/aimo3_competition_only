import os, sys, zipfile, runpy
from pathlib import Path

ZIP_NAME = "AIMO3_SUBMISSION.zip"

def find_zip():
roots = [Path("/kaggle/input"), Path.cwd()]
for root in roots:
if root.exists():
try:
for p in root.rglob(ZIP_NAME):
return p
except Exception:
pass
return None

zip_path = find_zip()
if not zip_path:
try:
inp = Path("/kaggle/input")
if inp.exists():
print("INPUT_DIRS=", [p.name for p in inp.iterdir()])
except Exception:
pass
raise FileNotFoundError(f"Missing {ZIP_NAME}; searched under /kaggle/input and CWD")

work = Path("/kaggle/working/submission")
work.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, "r") as z:
z.extractall(work)

gw = work / "kaggle_evaluation" / "aimo_3_gateway.py"
if not gw.exists():
raise FileNotFoundError(f"Missing gateway after extract: {gw}")

sys.path.insert(0, str(work))
os.chdir(str(work))
runpy.run_path(str(gw), run_name="**main**")