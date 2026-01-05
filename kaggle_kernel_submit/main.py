import os, sys, zipfile, shutil

def _find_submission_zip():
candidates = [
"/kaggle/input/aimo3-submission/AIMO3_SUBMISSION.zip",
"/kaggle/input/aimo3-submission/aimo3_submission.zip",
]
for p in candidates:
if os.path.exists(p):
return p
# fallback: scan /kaggle/input for any zip with AIMO3 in name
base = "/kaggle/input"
if os.path.isdir(base):
for root, *, files in os.walk(base):
for f in files:
fu = f.upper()
if fu.endswith(".ZIP") and "AIMO3" in fu:
return os.path.join(root, f)
raise FileNotFoundError("AIMO3_SUBMISSION_ZIP_NOT_FOUND_UNDER*/kaggle/input")

def _extract(zip_path: str) -> str:
outdir = "/kaggle/working/submission_pkg"
if os.path.exists(outdir):
shutil.rmtree(outdir)
os.makedirs(outdir, exist_ok=True)
with zipfile.ZipFile(zip_path, "r") as z:
z.extractall(outdir)
return outdir

def main():
# Kernel smoke: ensure dataset zip is readable + gateway compiles (no execution side effects)
zpath = _find_submission_zip()
pkg = _extract(zpath)

```
gw1 = os.path.join(pkg, "kaggle_evaluation", "aimo_3_gateway.py")
gw2 = os.path.join(os.path.dirname(__file__), "kaggle_evaluation", "aimo_3_gateway.py")
gw = gw1 if os.path.exists(gw1) else gw2 if os.path.exists(gw2) else None

if gw is None or not os.path.exists(gw):
    print("GATEWAY_NOT_FOUND")
    return 0

import py_compile
py_compile.compile(gw, doraise=True)
print("GATEWAY_COMPILE_OK")
return 0
```

if **name** == "**main**":
raise SystemExit(main())