import os, sys, zipfile, runpy
from pathlib import Path

DATASET_SLUG = "aimo3-submission"
ZIP_NAME = "AIMO3_SUBMISSION.zip"

zip_path = Path("/kaggle/input") / DATASET_SLUG / ZIP_NAME
if not zip_path.exists():
    # fallback: scan inputs (defensive)
    cand = list(Path("/kaggle/input").rglob(ZIP_NAME))
    if not cand:
        raise FileNotFoundError(f"Missing {ZIP_NAME} under /kaggle/input (expected {zip_path})")
    zip_path = cand[0]

work_dir = Path("/kaggle/working/submission")
if work_dir.exists():
    # clean deterministic
    for p in sorted(work_dir.rglob("*"), reverse=True):
        if p.is_file():
            p.unlink()
        else:
            try:
                p.rmdir()
            except OSError:
                pass
else:
    work_dir.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, "r") as z:
    z.extractall(work_dir)

gw = work_dir / "kaggle_evaluation" / "aimo_3_gateway.py"
if not gw.exists():
    raise FileNotFoundError(f"Missing gateway at {gw}")

# ensure submission package is importable
sys.path.insert(0, str(work_dir))

# run gateway as script entrypoint
runpy.run_path(str(gw), run_name="__main__")