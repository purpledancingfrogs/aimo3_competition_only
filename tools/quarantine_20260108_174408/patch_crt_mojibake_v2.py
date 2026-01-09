import re, pathlib

p = pathlib.Path("solver.py")
src = p.read_text(encoding="utf-8")

NORM2_B = "# === AUREON_NORM2_MOJIBAKE_BEGIN ==="
NORM2_E = "# === AUREON_NORM2_MOJIBAKE_END ==="
CRT_B   = "# === AUREON_CRT_BEGIN ==="
CRT_E   = "# === AUREON_CRT_END ==="

def insert_before_first_class(src: str, block: str) -> str:
    m = re.search(r'(?m)^class\s+Solver\b', src)
    if not m:
        raise RuntimeError("Could not find top-level 'class Solver' to insert before.")
    return src[:m.start()] + block + "\n\n" + src[m.start():]

def remove_block(src: str, b: str, e: str) -> str:
    if b in src and e in src:
        pat = re.compile(re.escape(b) + r".*?" + re.escape(e), re.S)
        src = pat.sub("", src, count=1)
    return src

# 1) Add/refresh _norm2
src = remove_block(src, NORM2_B, NORM2_E)
norm2_block = f"""{NORM2_B}
def _norm2(prompt: str) -> str:
    s = _norm(prompt)
    # common UTF-8->cp1252 mojibake from exported datasets
    s = (s.replace("â‰¡", "≡")
           .replace("â‰¤", "≤")
           .replace("â‰¥", "≥")
           .replace("Â", ""))
    return s
{NORM2_E}"""
src = insert_before_first_class(src, norm2_block)

# 2) Ensure Solver.solve uses _norm2(prompt)
# Replace the first occurrence of: s = _norm(prompt)
src, n = re.subn(r'(?m)^(\s*)s\s*=\s*_norm\(\s*prompt\s*\)\s*$',
                 r'\1s = _norm2(prompt)', src, count=1)
# If not found, do nothing (some versions may name the variable differently)

# 3) Add/refresh CRT helpers
src = remove_block(src, CRT_B, CRT_E)
crt_block = f"""{CRT_B}
def _egcd(a: int, b: int):
    if b == 0:
        return (abs(a), 1 if a >= 0 else -1, 0)
    g, x, y = _egcd(b, a % b)
    return (g, y, x - (a // b) * y)

def _inv_mod(a: int, m: int):
    a %= m
    g, x, _ = _egcd(a, m)
    if g != 1:
        return None
    return x % m

def _crt2(a: int, m: int, b: int, n: int):
    # solve x≡a (mod m), x≡b (mod n); return smallest nonnegative or None if inconsistent
    if m == 0 or n == 0:
        return None
    m = abs(int(m)); n = abs(int(n))
    a %= m; b %= n
    from math import gcd
    g = gcd(m, n)
    if (b - a) % g != 0:
        return None
    m1 = m // g
    n1 = n // g
    rhs = (b - a) // g
    inv = _inv_mod(m1, n1)
    if inv is None:
        return None
    t = (rhs * inv) % n1
    x = a + m * t
    l = m * n1
    return x % l

def _handle_crt(s: str):
    # accept "≡", mojibake "â‰¡", or plain "="
    s2 = s.replace("â‰¡", "≡")
    pat = re.compile(r'x\s*(?:≡|=)\s*([+-]?\d+)\s*\(mod\s*([+-]?\d+)\)', re.IGNORECASE)
    hits = pat.findall(s2)
    if len(hits) >= 2:
        a, m = int(hits[0][0]), int(hits[0][1])
        b, n = int(hits[1][0]), int(hits[1][1])
        ans = _crt2(a, m, b, n)
        if ans is not None:
            return str(ans)
    return None
{CRT_E}"""
src = insert_before_first_class(src, crt_block)

# 4) Wire CRT right after system_sum block (insert once)
if "out = _handle_crt(s)" not in src:
    pat = re.compile(
        r'(?s)(\n(?P<i>[ \t]*)out\s*=\s*_handle_system_sum\(s\)\s*\n'
        r'(?P<i2>[ \t]*)if\s+out\s+is\s+not\s+None:\s*\n'
        r'(?P<i3>[ \t]*)return\s+out\s*\n)'
    )
    m = pat.search(src)
    if not m:
        raise RuntimeError("Could not find system_sum return block to insert CRT after.")
    i1, i2, i3 = m.group("i"), m.group("i2"), m.group("i3")
    ins = f"{i1}out = _handle_crt(s)\n{i2}if out is not None:\n{i3}return out\n"
    src = src[:m.end(1)] + ins + src[m.end(1):]

p.write_text(src, encoding="utf-8")
print("PATCH_OK")
