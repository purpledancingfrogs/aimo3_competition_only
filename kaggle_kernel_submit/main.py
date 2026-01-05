import os, sys, zipfile, runpy
from pathlib import Path

DATASET_DIR = Path("/kaggle/input")
ZIP_NAME = "AIMO3_SUBMISSION.zip"

def find_zip():
    # Preferred expected path
    p = DATASET_DIR / "aimo3-submission" / ZIP_NAME
    if p.exists():
        return p
    # Fallback: search all mounted datasets (case-insensitive filename)
    if DATASET_DIR.exists():
        for d in DATASET_DIR.iterdir():
            if d.is_dir():
                cand = d / ZIP_NAME
                if cand.exists():
                    return cand
                # case-insensitive scan
                for f in d.iterdir():
                    if f.is_file() and f.name.lower() == ZIP_NAME.lower():
                        return f
    return None

def main():
    z = find_zip()
    if z is None:
        listing = []
        if DATASET_DIR.exists():
            for d in sorted(DATASET_DIR.glob("*")):
                if d.is_dir():
                    listing.append(str(d))
                    for f in sorted(d.glob("*")):
                        listing.append("  - " + str(f))
        raise FileNotFoundError(f"Missing {ZIP_NAME} under /kaggle/input (looked for /kaggle/input/*/{ZIP_NAME}). Listing:\\n" + "\\n".join(listing))

    work = Path("/kaggle/working/submission")
    work.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(str(z), "r") as zf:
        zf.extractall(str(work))

    gw = work / "kaggle_evaluation" / "aimo_3_gateway.py"
    if not gw.exists():
        raise FileNotFoundError(f"Extracted zip but missing gateway at {gw}")

    sys.path.insert(0, str(work))
    runpy.run_path(str(gw), run_name="__main__")

if __name__ == "__main__":
    main()