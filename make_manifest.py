import hashlib, subprocess, sys, json
from pathlib import Path

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()

Path("audit").mkdir(exist_ok=True)

files = [
    "solver.py","run_all.py","run.py",
    "submission.csv","audit_test.csv",
    "eval_report.csv","eval_train.py",
    "audit/python_version.txt","audit/pip_version.txt","audit/pip_freeze.txt","audit/eval_summary.json"
]

def rev(x):
    return subprocess.check_output(["git","rev-parse",x]).decode().strip()

manifest = {
    "git_head": rev("HEAD"),
    "tag_audit_pass_v1": rev("audit-pass-v1"),
    "python": sys.version.replace("\n"," "),
    "files": {}
}

for fp in files:
    p = Path(fp)
    if p.exists():
        manifest["files"][fp] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}

Path("audit/AUDIT_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print("WROTE audit/AUDIT_MANIFEST.json")
