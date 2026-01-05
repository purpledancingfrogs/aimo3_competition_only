import pathlib, re

p = pathlib.Path("solver.py")
s = p.read_text(encoding="utf-8")

# Remove any broken/duplicated __main__ block at the end (common source of bad indentation).
# Keep everything before the FIRST occurrence of an __main__ guard near the bottom.
main_pat = re.compile(r"\nif\s+__name__\s*==\s*[\"']__main__[\"']\s*:\s*\n", re.M)
m = None
for mm in main_pat.finditer(s):
    m = mm  # take last
if m:
    head = s[:m.start()]
else:
    head = s

# Strip trailing whitespace/newlines to avoid accidental indentation carryover
head = head.rstrip() + "\n\n"

# Add a clean deterministic CLI entrypoint that matches Kaggle-style stdin->stdout use
tail = r'''if __name__ == "__main__":
    import sys
    data = sys.stdin.read()
    # Prefer solve(text) if present; otherwise fallback to Solver().solve(text)
    if "solve" in globals() and callable(globals()["solve"]):
        out = globals()["solve"](data)
    else:
        out = Solver().solve(data)
    sys.stdout.write(str(out).strip())
    sys.stdout.write("\n")
'''
p.write_text(head + tail, encoding="utf-8")
print("FIXED solver.py __main__ block")
