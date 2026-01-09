import re, pathlib

p = pathlib.Path("solver.py")
src = p.read_text(encoding="utf-8")

# ---------- helpers to insert blocks safely ----------
def insert_before_first(pattern: str, block: str) -> str:
    m = re.search(pattern, src, flags=re.M)
    if not m:
        raise RuntimeError(f"pattern not found: {pattern}")
    i = m.start()
    return src[:i] + block + "\n\n" + src[i:]

def ensure_block(marker_begin: str, marker_end: str, block: str) -> str:
    if marker_begin in src and marker_end in src:
        return src
    # insert before the real Solver class (first top-level class Solver)
    return re.sub(r'(?m)^class\s+Solver\b', block + "\n\nclass Solver", src, count=1)

def replace_first(regex: str, repl: str) -> str:
    return re.sub(regex, repl, src, count=1, flags=re.M)

def insert_after_system_sum(block: str) -> str:
    # Insert right after:
    # out = _handle_system_sum(s)
    # if out is not None:
    #     return out
    pat = r'(\n(?P<i>[ \t]*)out\s*=\s*_handle_system_sum\(s\)\s*\n(?P<i2>[ \t]*)if\s+out\s+is\s+not\s+None:\s*\n(?P<i3>[ \t]*)return\s+out\s*\n)'
    m = re.search(pat, src, flags=re.S)
    if not m:
        raise RuntimeError("system_sum block not found")
    i = m.end(1)
    i1 = m.group("i")
    i2 = m.group("i2")
    i3 = m.group("i3")
    ins = f"{i1}out = _handle_crt(s)\n{i2}if out is not None:\n{i3}return out\n"
    return src[:i] + ins + src[i:]

# ---------- (A) add mojibake normalization wrapper ----------
NORM2_BEGIN = "# === AUREON_NORM2_MOJIBAKE_BEGIN ==="
NORM2_END   = "# === AUREON_NORM2_MOJIBAKE_END ==="
CRT_BEGIN   = "# === AUREON_CRT_BEGIN ==="
CRT_END     = "# === AUREON_CRT_END ==="

norm2_block = f"""{NORM2_BEGIN}
def _norm2(prompt: str) -> str:
    s = _norm(prompt)
    # UTF-8 -> cp1252 mojibake sequences expressed via escapes (ASCII-only source)
    s = (s.replace("\\u00e2\\u2030\\u00a1", "\\u2261")  # â‰¡ -> ≡
           .replace("\\u00e2\\u2030\\u00a4", "\\u2264")  # â‰¤ -> ≤
           .replace("\\u00e2\\u2030\\u00a5", "\\u2265")  # â‰¥ -> ≥
           .replace("\\u00c2", ""))                      # stray Â
    return s
{NORM2_END}"""

src2 = src
if NORM2_BEGIN not in src2:
    src2 = re.sub(r'(?m)^class\s+Solver\b', norm2_block + "\n\nclass Solver", src2, count=1)

# ensure Solver.solve uses _norm2
src2 = re.sub(r'(?m)^(\s*)s\s*=\s*_norm\(\s*prompt\s*\)\s*$',
              r'\1s = _norm2(prompt)', src2, count=1)

# ---------- (B) add CRT handler ----------
crt_block = f"""{CRT_BEGIN}
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
    # solve x≡a (mod m), x≡b (mod n); return smallest nonnegative or None
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
    # accept ≡ and the mojibake version â‰¡ via escapes
    # after _norm2(), mojibake should already be fixed, but keep both for safety
    import re
    s2 = s.replace("\\u00e2\\u2030\\u00a1", "\\u2261")
    pat = re.compile(r'x\\s*(?:\\u2261|=)\\s*([+-]?\\d+)\\s*\\(mod\\s*([+-]?\\d+)\\)', re.IGNORECASE)
    hits = pat.findall(s2)
    if len(hits) >= 2:
        a, m = int(hits[0][0]), int(hits[0][1])
        b, n = int(hits[1][0]), int(hits[1][1])
        ans = _crt2(a, m, b, n)
        if ans is not None:
            return str(ans)
    return None
{CRT_END}"""

if CRT_BEGIN not in src2:
    src2 = re.sub(r'(?m)^class\s+Solver\b', crt_block + "\n\nclass Solver", src2, count=1)

# wire CRT after system_sum once
if "_handle_crt" in src2 and "out = _handle_crt(s)" not in src2:
    # operate on src2 by temporarily binding global
    src = src2
    src2 = insert_after_system_sum("")  # returns src with insertion using current 'src' variable
    # the function above inserts nothing if block arg empty; so do direct insertion:
    pat = r'(\n(?P<i>[ \t]*)out\s*=\s*_handle_system_sum\(s\)\s*\n(?P<i2>[ \t]*)if\s+out\s+is\s+not\s+None:\s*\n(?P<i3>[ \t]*)return\s+out\s*\n)'
    m = re.search(pat, src2, flags=re.S)
    if not m:
        raise RuntimeError("system_sum block not found (post)")
    i = m.end(1)
    i1, i2, i3 = m.group("i"), m.group("i2"), m.group("i3")
    ins = f"{i1}out = _handle_crt(s)\n{i2}if out is not None:\n{i3}return out\n"
    src2 = src2[:i] + ins + src2[i:]

# write back
p.write_text(src2, encoding="utf-8")
print("PATCH_OK")
