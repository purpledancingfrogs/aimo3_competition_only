import io, os, re, sys, time, json, pathlib, contextlib, threading

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = [
  ROOT/"solver.py",
  ROOT/"kaggle_evaluation"/"aimo_3_gateway.py",
  ROOT/"kaggle_evaluation"/"aimo_3_inference_server.py",
  ROOT/"requirements.txt",
]

FORBIDDEN_SUBSTRINGS = [
  "requests.", "urllib.", "http://", "https://", "socket.", "ftplib.",
  "subprocess.", "os.system(", "powershell", "curl ", "wget ", "pip install",
]

PRINT_RE = re.compile(r'^\s*print\s*\(', re.M)
DIGITS_ONLY = re.compile(r'^\d+$')

def fail(msg: str):
  print(msg)
  raise SystemExit(1)

def ok(msg: str):
  print(msg)

def read_text_strict(p: pathlib.Path) -> str:
  b = p.read_bytes()
  # hard fail if UTF-8 BOM exists anywhere
  if b.startswith(b"\xef\xbb\xbf") or (b"\xef\xbb\xbf" in b):
    fail(f"FAIL: UTF8_BOM_PRESENT: {p.as_posix()}")
  t = b.decode("utf-8", errors="strict")
  if "\ufeff" in t:
    fail(f"FAIL: FEFF_PRESENT: {p.as_posix()}")
  return t

def run_with_timeout(fn, timeout_s: float):
  res = {"ok": False, "val": None, "err": None}
  def _t():
    try:
      res["val"] = fn()
      res["ok"] = True
    except BaseException as e:
      res["err"] = repr(e)
  th = threading.Thread(target=_t, daemon=True)
  th.start()
  th.join(timeout_s)
  if th.is_alive():
    return (False, None, "TimeoutError")
  if not res["ok"]:
    return (False, None, res["err"])
  return (True, res["val"], None)

def main():
  missing = [str(p) for p in FILES if not p.exists()]
  if missing:
    fail("FAIL: MISSING_FILES:\n" + "\n".join(missing))

  contents = {p: read_text_strict(p) for p in FILES}

  sol = contents[ROOT/"solver.py"]
  gw  = contents[ROOT/"kaggle_evaluation"/"aimo_3_gateway.py"]

  # A) gateway must silence stdout/stderr during imports or per-call
  if ("redirect_stdout" not in gw) or ("redirect_stderr" not in gw):
    fail("FAIL[A]: gateway missing redirect_stdout/redirect_stderr")

  # B) gateway must coerce to int (_to_i64 present)
  if not re.search(r"def\s+_to_i64\s*\(", gw):
    fail("FAIL[B]: gateway missing _to_i64")
  if not (("int(" in gw) or ("int64" in gw)):
    fail("FAIL[B]: gateway does not clearly coerce to int/int64")

  # C) determinism: forbid mtime/getmtime usage anywhere in solver
  if ("getmtime" in sol) or re.search(r"\bmtime\b", sol):
    fail("FAIL[C]: solver contains mtime/getmtime (nondeterministic risk)")

  # E) resource: forbid simplify()
  if re.search(r"\bsympy\.simplify\b|\bsimplify\s*\(", sol):
    fail("FAIL[E]: solver uses simplify()")

  # F) parsing: require NFKC + zero-width cleanup intent
  if ("unicodedata.normalize(\"NFKC\"" not in sol) and ("unicodedata.normalize('NFKC'" not in sol):
    fail("FAIL[F]: solver missing NFKC normalization")
  if not (("\\u200b" in sol) or ("\u200b" in sol) or ("zero-width" in sol.lower())):
    fail("FAIL[F]: solver missing explicit zero-width handling (u200b/zero-width)")

  # Global forbidden substrings
  for p,t in contents.items():
    for s in FORBIDDEN_SUBSTRINGS:
      if s in t:
        fail(f"FAIL[GLOBAL]: forbidden substring '{s}' in {p.as_posix()}")

  # Prints forbidden in submission-critical files
  for p,t in contents.items():
    if PRINT_RE.search(t):
      fail(f"FAIL[GLOBAL]: print() found in {p.as_posix()}")

  # Disallow solver reading local datasets (hidden-data compliance paranoia)
  for needle in ["reference.csv", "kaggle_data", "AIMO3_Reference_Problems", "tools/reference_problems.jsonl"]:
    if needle in sol:
      fail(f"FAIL[GLOBAL]: solver references local dataset path '{needle}'")

  # Dynamic: import solver must produce no stdout/stderr
  buf = io.StringIO()
  with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
    ok_imp, _, err = run_with_timeout(lambda: __import__("solver"), 5.0)
  if not ok_imp:
    fail(f"FAIL[DYN]: solver import failed: {err}")
  if buf.getvalue().strip():
    fail("FAIL[A]: stdout/stderr pollution during solver import")

  import solver  # noqa

  def call_solve(s: str) -> str:
    b = io.StringIO()
    with contextlib.redirect_stdout(b), contextlib.redirect_stderr(b):
      r = solver.solve(s)
    out = b.getvalue().strip()
    if out:
      raise RuntimeError("stdout_pollution")
    return "" if r is None else str(r).strip()

  prompts = [
    "Solve: x âˆ’ 5 = 0. Return integer only.",
    "Solve: 2x+3=11. Return integer only.",
    "Solve: -3x = -6. Return integer only.",
    "Solve: xÂ² + 2x + 1 = 0. Return integer only.",
    "Solve: x^2 = 1. Return a single integer only.",
    "Solve system: x+y=3, x-y=1. Return x+y as integer only.",
    "Solve system: 7*x + 6*y = 41 and 5*x - 2*y = 9. Return x+y only.",
    "Compute gcd(-12,18). Return integer only.",
    "Compute lcm(4,6). Return integer only.",
    "Compute 2^100000 mod 3. Return integer only.",
    "Find x â‰¡ âˆ’1 (mod 1000). Return integer only.",
    "Find x â‰¡ 1 (mod -7). Return integer only.",
    "Compute floor(-1.1). Return integer only.",
    "Compute ceil(-1.1). Return integer only.",
    "Compute 1/2 + 1/3, then multiply by 6. Return integer only.",
    "Remove zero-width: 1\u200b2\u200b3 -> interpret as 123. Return integer only.",
    "Thin space: 1000\u2009000 -> interpret as 1000000. Return integer only.",
    "Superscripts: 2Â³ + 3Â². Return integer only.",
    "Unicode fullwidth multiply: 2ï¼Šy=6 with y integer. Return y only.",
    ("A"*10000) + " = 1",
  ]

  for i,p in enumerate(prompts, 1):
    ok_run, val, err = run_with_timeout(lambda p=p: call_solve(p), 2.5)
    if not ok_run:
      fail(f"FAIL[DYN]: solve timeout/error on prompt #{i}: {err}")
    if not val:
      fail(f"FAIL[DYN]: empty answer on prompt #{i}")
    if not DIGITS_ONLY.match(val):
      fail(f"FAIL[DYN]: non-digit output on prompt #{i}: {val!r}")
    n = int(val)
    if not (0 <= n <= 999):
      fail(f"FAIL[DYN]: out-of-range (0..999) on prompt #{i}: {n}")

    # Determinism check: repeated calls identical
    v2 = call_solve(p)
    v3 = call_solve(p)
    if v2 != val or v3 != val:
      fail(f"FAIL[C]: nondeterministic output on prompt #{i}: {val!r} vs {v2!r} vs {v3!r}")

  ok("PASS: PASSFAIL_ARENA_OK")
  return 0

if __name__ == "__main__":
  sys.exit(main())