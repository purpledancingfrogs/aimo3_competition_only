import sys
import yaml
import subprocess
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).parent.resolve()
ARTIFACTS = ROOT / "artifacts"

def load_registry():
    with open(ROOT / "execution_set.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["executors"]

def list_executors():
    for k in load_registry().keys():
        print(k)

def run(name):
    reg = load_registry()
    if name not in reg:
        raise SystemExit(f"Executor '{name}' not found")
    exe = reg[name]
    path = ROOT / exe["path"]
    entry = exe["entry"]
    subprocess.check_call(
        [sys.executable, entry],
        cwd=path
    )

def verify(name):
    p = ARTIFACTS / name
    if not p.exists():
        raise SystemExit("No artifacts to verify")
    h = hashlib.sha256()
    for f in sorted(p.rglob("*")):
        if f.is_file():
            h.update(f.read_bytes())
    print(h.hexdigest())

def main():
    if len(sys.argv) < 2:
        raise SystemExit("command required")
    cmd = sys.argv[1]
    if cmd == "list":
        list_executors()
    elif cmd == "run":
        run(sys.argv[2])
    elif cmd == "verify":
        verify(sys.argv[2])
    else:
        raise SystemExit("unknown command")

if __name__ == "__main__":
    main()
