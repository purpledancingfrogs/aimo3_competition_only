import argparse, hashlib, os, subprocess, zipfile

FILES = [
  "solver.py",
  "kaggle_evaluation/aimo_3_gateway.py",
  "kaggle_evaluation/aimo_3_inference_server.py",
  "requirements.txt",
]

FIXED_DT = (1980, 1, 1, 0, 0, 0)

def git_blob_bytes(path: str) -> bytes:
  p = path.replace("\\", "/")
  return subprocess.check_output(["git", "show", f"HEAD:{p}"])

def sha256_hex(b: bytes) -> str:
  return hashlib.sha256(b).hexdigest().upper()

def write_blob_hashes(out_path: str) -> None:
  lines = []
  for p in FILES:
    b = git_blob_bytes(p)
    lines.append(f"{sha256_hex(b)}  {p}")
  with open(out_path, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines) + "\n")

def build_deterministic_zip(zip_out: str) -> None:
  os.makedirs(os.path.dirname(zip_out), exist_ok=True)
  with zipfile.ZipFile(zip_out, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as z:
    for p in FILES:
      arc = p.replace("\\", "/")
      b = git_blob_bytes(p)
      zi = zipfile.ZipInfo(filename=arc, date_time=FIXED_DT)
      zi.compress_type = zipfile.ZIP_STORED
      zi.create_system = 0
      zi.external_attr = 0
      z.writestr(zi, b)

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--zip_out", required=True)
  ap.add_argument("--hash_out", required=True)
  args = ap.parse_args()
  write_blob_hashes(args.hash_out)
  build_deterministic_zip(args.zip_out)

if __name__ == "__main__":
  main()
