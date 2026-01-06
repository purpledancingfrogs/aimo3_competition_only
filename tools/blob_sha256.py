#!/usr/bin/env python3
import argparse, hashlib, subprocess

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rev", default="HEAD")
    ap.add_argument("--paths", nargs="*", default=SUBMIT_FILES)
    args = ap.parse_args()
    for p in sorted(args.paths):
        data = git_show_bytes(args.rev, p)
        print(f"{sha256_hex(data)}  {p}  (git_blob)")

if __name__ == "__main__":
    main()
