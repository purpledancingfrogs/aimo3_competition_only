#!/usr/bin/env python3
import argparse, hashlib, os, subprocess, zipfile

FIXED_DT = (1980, 1, 1, 0, 0, 0)

SUBMIT_FILES = [
    "solver.py",
    "kaggle_evaluation/aimo_3_gateway.py",
    "kaggle_evaluation/aimo_3_inference_server.py",
    "requirements.txt",
]

def git_show_bytes(rev: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{rev}:{path}"], stderr=subprocess.STDOUT)

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest().upper()

def build(rev: str, out_path: str):
    paths = sorted(SUBMIT_FILES)
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    tmp = out_path + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)

    entries = []
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.comment = b"DETERMINISTIC_AIMO3_SUBMISSION_ZIP_V1"
        for p in paths:
            data = git_show_bytes(rev, p)
            zi = zipfile.ZipInfo(filename=p, date_time=FIXED_DT)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.create_system = 3
            zi.external_attr = (0o644 & 0xFFFF) << 16
            zf.writestr(zi, data)
            entries.append((p, sha256_hex(data), len(data)))

    os.replace(tmp, out_path)
    zbytes = open(out_path, "rb").read()
    print(f"ZIP_SHA256={sha256_hex(zbytes)}")
    for p,h,n in entries:
        print(f"BLOB_SHA256={h}  SIZE={n}  PATH={p}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rev", default="HEAD")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    build(args.rev, args.out)

if __name__ == "__main__":
    main()
