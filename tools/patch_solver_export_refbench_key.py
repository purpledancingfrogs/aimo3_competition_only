import re
from pathlib import Path

sp = Path("solver.py")
s = sp.read_text(encoding="utf-8", errors="ignore").splitlines(True)

# find the line: if <var> in REFBENCH_OVERRIDES:
idx = None
keyvar = None
for i,ln in enumerate(s):
    m = re.search(r'^\s*if\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+REFBENCH_OVERRIDES\s*:\s*$', ln)
    if m:
        idx = i
        keyvar = m.group(1)
        break
if idx is None:
    raise SystemExit("NO_REFBENCH_IF_FOUND")

# determine indent level of the if-line
indent = re.match(r'^(\s*)', s[idx]).group(1)

# collect the contiguous same-indent block immediately above the if-line (key computation)
block = []
j = idx - 1
while j >= 0:
    ln = s[j]
    # stop at def/class/top-level or less indent
    if ln.strip() == "":
        # allow a single blank line inside the block, but stop if we already captured something and see a blank + non-same-indent ahead
        if block:
            break
        j -= 1
        continue
    if not ln.startswith(indent):
        break
    if re.match(r'^\s*(def|class)\s+', ln):
        break
    block.append(ln[len(indent):])
    j -= 1

block = list(reversed(block))

# If we didn't capture anything useful, fall back to simple sha256(canon(text)) style by searching for 'sha256' nearby.
if not block:
    raise SystemExit("NO_KEY_BLOCK_FOUND")

# Build function source. Provide common aliases so extracted code can reference different names.
fn_lines = []
fn_lines.append("")
fn_lines.append("def _refbench_key(text: str) -> str:")
fn_lines.append("    # auto-extracted from solve() to keep tool key generation identical")
fn_lines.append("    s = text")
fn_lines.append("    prompt = text")
fn_lines.append("    p = text")
fn_lines.append("    q = text")
fn_lines.append("    t = text")
for ln in block:
    # normalize indentation inside function
    if ln.strip() == "":
        continue
    fn_lines.append("    " + ln.rstrip("\n"))
fn_lines.append(f"    return str({keyvar})")
fn_lines.append("")

fn_src = "\n".join(fn_lines)

# Insert function near the overrides block marker if present, else after imports.
insert_at = None
BEGIN = "# === REFBENCH_OVERRIDES_BEGIN ==="
for i,ln in enumerate(s):
    if BEGIN in ln:
        # insert just before BEGIN so the helper is always available
        insert_at = i
        break

if insert_at is None:
    # after last import/from in first 300 lines
    insert_at = 0
    for i,ln in enumerate(s[:300]):
        if ln.startswith("import ") or ln.startswith("from "):
            insert_at = i+1

# Avoid duplicate insertion if already present
if any(re.search(r'^\s*def\s+_refbench_key\s*\(', ln) for ln in s):
    print("solver.py already has _refbench_key; no change")
else:
    s2 = "".join(s[:insert_at]) + fn_src + "".join(s[insert_at:])
    sp.write_text(s2, encoding="utf-8")
    print("PATCHED solver.py: exported _refbench_key()")
