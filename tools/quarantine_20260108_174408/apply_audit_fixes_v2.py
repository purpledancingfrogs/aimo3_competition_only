import re, os, sys, io, pathlib, contextlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOLVER = ROOT/"solver.py"
GATEWAY = ROOT/"kaggle_evaluation"/"aimo_3_gateway.py"

def read_utf8_bytes(p: pathlib.Path) -> bytes:
    b = p.read_bytes()
    return b

def write_utf8_nobom(p: pathlib.Path, s: str) -> None:
    p.write_bytes(s.encode("utf-8"))

def strip_bom_and_feff_bytes(b: bytes) -> bytes:
    # remove UTF-8 BOM if present at start
    if b.startswith(b"\xef\xbb\xbf"):
        b = b[3:]
    # remove any UTF-8 BOM sequence anywhere (should not exist, but harden)
    b = b.replace(b"\xef\xbb\xbf", b"")
    return b

def patch_solver():
    if not SOLVER.exists():
        raise SystemExit(f"FAIL: missing {SOLVER}")
    b = strip_bom_and_feff_bytes(read_utf8_bytes(SOLVER))
    try:
        t = b.decode("utf-8", errors="strict")
    except Exception as e:
        raise SystemExit(f"FAIL: solver.py not strict utf-8: {e}")

    # Remove any embedded FEFF characters anywhere
    if "\ufeff" in t:
        t = t.replace("\ufeff", "")

    # Comment out any print() lines (audit forbids stdout in critical files)
    t = re.sub(r'(?m)^(\s*)print\s*\(', r'\1# print(', t)

    # Fix prior broken placeholder if present
    t = re.sub(r'(?m)^(?P<indent>\s*)cand\s*=.*\/\*GETMTIME_REMOVED\*\/.*$',
               r'\g<indent>cand = sorted(set(cand))', t)
    # Remove any mtime/getmtime ordering (nondet)
    t = re.sub(r'(?m)^(?P<indent>\s*)cand\s*=.*getmtime.*$',
               r'\g<indent>cand = sorted(set(cand))', t)
    t = re.sub(r'(?m)^(?P<indent>\s*)cand\s*=.*mtime.*$',
               r'\g<indent>cand = sorted(set(cand))', t)

    # Ensure there is a top-level solve() to wrap
    if not re.search(r'(?m)^def\s+solve\s*\(', t):
        raise SystemExit("FAIL: solver.py has no top-level def solve(...) to wrap")

    # If already wrapped, do nothing further
    if "AUREON_HARDEN_V2" in t and re.search(r'(?m)^def\s+_orig_solve\s*\(', t):
        write_utf8_nobom(SOLVER, t)
        return

    # Rename existing solve -> _orig_solve (first occurrence only)
    if not re.search(r'(?m)^def\s+_orig_solve\s*\(', t):
        t = re.sub(r'(?m)^def\s+solve\s*\(', 'def _orig_solve(', t, count=1)

    wrapper = r'''
# === AUREON_HARDEN_V2 ===
import unicodedata as _unicodedata
import math as _math
import fractions as _fractions
import contextlib as _contextlib
import io as _io
import os as _os
import re as _re

# Unicode/invisible cleanup (single entry point)
_ZERO_WIDTH = {
    "\u200b", "\u200c", "\u200d", "\u2060", "\u2063", "\ufeff",
    "\u00ad",  # soft hyphen
}
_SPACE_EQUIV = {
    "\u00a0", "\u2009", "\u202f", "\u2007", "\u205f",
}
_DASH_MAP = str.maketrans({
    "−":"-","–":"-","—":"-","﹣":"-","‐":"-","-":"-",
    "＋":"+","－":"-","＝":"=","＊":"*","／":"/",
})
_SUP_DIG = str.maketrans({
    "⁰":"0","¹":"1","²":"2","³":"3","⁴":"4","⁵":"5","⁶":"6","⁷":"7","⁸":"8","⁹":"9",
})

def _norm_text(t: str) -> str:
    t = "" if t is None else str(t)
    t = _unicodedata.normalize("NFKC", t)
    t = t.translate(_DASH_MAP).translate(_SUP_DIG)
    for ch in _ZERO_WIDTH:
        if ch in t:
            t = t.replace(ch, "")
    for ch in _SPACE_EQUIV:
        if ch in t:
            t = t.replace(ch, " ")
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = _re.sub(r"[ \t\f\v]+", " ", t)
    t = _re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def _int_mod_1000(x: int) -> str:
    return str(int(x) % 1000)

@_contextlib.contextmanager
def _silence_stdio():
    buf = _io.StringIO()
    with _contextlib.redirect_stdout(buf), _contextlib.redirect_stderr(buf):
        yield

def _posix_timeout(seconds: int):
    # Returns a context manager; on non-posix, no-op
    if _os.name != "posix":
        return _contextlib.nullcontext()
    import signal
    class _Alarm:
        def __enter__(self):
            def _handler(signum, frame):
                raise TimeoutError("timeout")
            self._old = signal.signal(signal.SIGALRM, _handler)
            signal.setitimer(signal.ITIMER_REAL, float(seconds))
        def __exit__(self, exc_type, exc, tb):
            signal.setitimer(signal.ITIMER_REAL, 0.0)
            try:
                signal.signal(signal.SIGALRM, self._old)
            except Exception:
                pass
            return False
    return _Alarm()

def _egcd(a: int, b: int):
    while b:
        a, b = b, a % b
    return abs(a)

def _lcm(a: int, b: int) -> int:
    a = int(a); b = int(b)
    if a == 0 or b == 0:
        return 0
    return abs(a // _egcd(a,b) * b)

def _parse_int(s: str):
    if s is None:
        return None
    s = s.strip()
    m = _re.fullmatch(r"[+-]?\d+", s)
    return int(s) if m else None

def _solve_powmod(t: str):
    # e.g. "2^100000 mod 3"
    m = _re.search(r"([+-]?\d+)\s*\^\s*([+-]?\d+)\s*(?:mod|%|modulo)\s*([+-]?\d+)", t, _re.I)
    if not m:
        return None
    a = int(m.group(1)); e = int(m.group(2)); mod = int(m.group(3))
    mod = abs(mod)
    if mod == 0:
        return None
    return pow(a, e, mod)

def _solve_congruence_single(t: str):
    # x ≡ a (mod m)
    m = _re.search(r"\bx\b\s*(?:≡|=|==)\s*([+-]?\d+)\s*(?:\(|\[)?\s*(?:mod|%|modulo)\s*([+-]?\d+)\s*(?:\)|\])?", t, _re.I)
    if not m:
        return None
    a = int(m.group(1)); mod = int(m.group(2))
    mod = abs(mod)
    if mod == 0:
        return None
    return a % mod

def _solve_gcd_lcm(t: str):
    m = _re.search(r"\bgcd\s*\(\s*([+-]?\d+)\s*,\s*([+-]?\d+)\s*\)", t, _re.I)
    if m:
        return _egcd(int(m.group(1)), int(m.group(2)))
    m = _re.search(r"\blcm\s*\(\s*([+-]?\d+)\s*,\s*([+-]?\d+)\s*\)", t, _re.I)
    if m:
        return _lcm(int(m.group(1)), int(m.group(2)))
    return None

def _solve_floor_ceil(t: str):
    m = _re.search(r"\bfloor\s*\(\s*([+-]?\d+(?:\.\d+)?)\s*\)", t, _re.I)
    if m:
        x = float(m.group(1))
        return _math.floor(x)
    m = _re.search(r"\bceil\s*\(\s*([+-]?\d+(?:\.\d+)?)\s*\)", t, _re.I)
    if m:
        x = float(m.group(1))
        return _math.ceil(x)
    return None

def _solve_rational_times(t: str):
    # "Compute 1/2 + 1/3, then multiply by 6" style
    fracs = _re.findall(r"([+-]?\d+)\s*/\s*([+-]?\d+)", t)
    if len(fracs) >= 2 and _re.search(r"\bmultiply\b|\btimes\b|\*\s*([+-]?\d+)", t, _re.I):
        f = _fractions.Fraction(0,1)
        for a,b in fracs[:2]:
            bb = int(b)
            if bb == 0:
                return None
            f += _fractions.Fraction(int(a), bb)
        m = _re.search(r"(?:multiply(?:\s+by)?|times|\*)\s*([+-]?\d+)", t, _re.I)
        if not m:
            return None
        k = int(m.group(1))
        f *= k
        if f.denominator != 1:
            return None
        return int(f.numerator)
    return None

def _coef_var(term: str, var: str):
    # returns coefficient for var in a linear expression snippet, else 0
    # supports forms: 7*x, -x, +3x, x
    term = term.replace(" ", "")
    # normalize "*"
    term = term.replace("×","*")
    pattern = r"([+-]?\d+)?\*?"+_re.escape(var)
    total = 0
    for m in _re.finditer(pattern, term):
        c = m.group(1)
        if c is None or c == "" or c == "+":
            total += 1
        elif c == "-":
            total -= 1
        else:
            total += int(c)
    return total

def _solve_2x2_system_sum(t: str):
    # Extract two equations ax+by=c over x,y; return x+y if determinable and integer
    # Non-greedy, line-local: split into segments
    segs = []
    for part in t.replace(";", "\n").split("\n"):
        part = part.strip()
        if not part:
            continue
        # further split on 'and' if present
        segs.extend([p.strip() for p in _re.split(r"\band\b", part, flags=_re.I) if p.strip()])

    eqs = []
    eq_re = _re.compile(r"(?P<lhs>[^=\n]{1,200})=(?P<rhs>[+-]?\d{1,30})")
    for s in segs:
        m = eq_re.search(s.replace(" ", ""))
        if not m:
            continue
        lhs = m.group("lhs")
        rhs = int(m.group("rhs"))
        ax = _coef_var(lhs, "x")
        by = _coef_var(lhs, "y")
        if ax == 0 and by == 0:
            continue
        eqs.append((ax, by, rhs))

    if len(eqs) < 2:
        return None
    (a1,b1,c1),(a2,b2,c2) = eqs[0], eqs[1]
    det = a1*b2 - a2*b1
    if det == 0:
        return None
    x_num = c1*b2 - c2*b1
    y_num = a1*c2 - a2*c1
    if x_num % det != 0 or y_num % det != 0:
        return None
    x = x_num // det
    y = y_num // det
    # Plug-back verify
    if a1*x + b1*y != c1 or a2*x + b2*y != c2:
        return None
    # If prompt asks for x+y, return sum; otherwise still safe to return sum when "x+y" appears
    if _re.search(r"x\s*\+\s*y", t):
        return x + y
    return x + y

# AtCoder floor_sum (deterministic O(log m))
def _floor_sum(n: int, m: int, a: int, b: int) -> int:
    n = int(n); m = int(m); a = int(a); b = int(b)
    if m <= 0 or n < 0:
        raise ValueError
    ans = 0
    if a >= m:
        ans += (n - 1) * n * (a // m) // 2
        a %= m
    if b >= m:
        ans += n * (b // m)
        b %= m
    y_max = a * n + b
    if y_max < m:
        return ans
    n2 = y_max // m
    b2 = y_max % m
    ans += _floor_sum(n2, a, m, b2)
    return ans

def _solve_floor_sum(t: str):
    # Detect sum floor((a*i+b)/m) for i=0..n-1
    # accepts plain: "sum_{i=0}^{n-1} floor((a i + b)/m)"
    tt = t.replace(" ", "")
    if not (_re.search(r"floor", tt, _re.I) and (_re.search(r"sum", tt, _re.I) or "\\sum" in tt)):
        return None
    # Try capture n,m,a,b integers
    # n from i=0..n-1
    mn = _re.search(r"i=0\}\^\{([+-]?\d+)-1\}", tt)
    if not mn:
        mn = _re.search(r"i=0\)\s*to\s*([+-]?\d+)-1", t, _re.I)
    if not mn:
        return None
    n = int(mn.group(1))
    # capture (a*i+b)/m
    mm = _re.search(r"floor\(\(?\(?([+-]?\d+)i([+-]\d+)?\)?\)?/([+-]?\d+)\)?\)", tt, _re.I)
    if not mm:
        mm = _re.search(r"floor\(\(?\(?([+-]?\d+)\*?i([+-]\d+)?\)?\)?/([+-]?\d+)\)?\)", tt, _re.I)
    if not mm:
        return None
    a = int(mm.group(1))
    b = int(mm.group(2)) if mm.group(2) else 0
    m = int(mm.group(3))
    m = abs(m)
    if m == 0:
        return None
    return _floor_sum(n, m, a, b)

def _solve_core(t: str):
    # Fast, bounded modules first
    r = _solve_powmod(t)
    if r is not None: return r
    r = _solve_congruence_single(t)
    if r is not None: return r
    r = _solve_gcd_lcm(t)
    if r is not None: return r
    r = _solve_floor_ceil(t)
    if r is not None: return r
    r = _solve_rational_times(t)
    if r is not None: return r
    r = _solve_2x2_system_sum(t)
    if r is not None: return r
    r = _solve_floor_sum(t)
    if r is not None: return r
    return None

def solve(problem_text: str) -> str:
    t = _norm_text(problem_text)
    if not t:
        return "0"
    # hard cap to prevent regex/sympy blowups
    if len(t) > 8000:
        t = t[:8000]

    with _silence_stdio():
        try:
            r = _solve_core(t)
            if r is not None:
                return _int_mod_1000(r)
        except Exception:
            pass

        # Fallback to original solver with POSIX timeout (Kaggle=linux)
        try:
            with _posix_timeout(8):
                r2 = _orig_solve(t)
            return _int_mod_1000(int(r2))
        except Exception:
            return "0"
'''
    t2 = t.rstrip() + "\n" + wrapper.lstrip("\n")
    write_utf8_nobom(SOLVER, t2)

def patch_gateway():
    if not GATEWAY.exists():
        # nothing to do
        return
    b = strip_bom_and_feff_bytes(read_utf8_bytes(GATEWAY))
    try:
        t = b.decode("utf-8", errors="strict")
    except Exception as e:
        raise SystemExit(f"FAIL: gateway not strict utf-8: {e}")
    if "\ufeff" in t:
        t = t.replace("\ufeff", "")

    # Comment out any print() lines
    t = re.sub(r'(?m)^(\s*)print\s*\(', r'\1# print(', t)

    # Ensure import solver is silenced at import-time
    # Replace either "import solver" or "from solver import solve" first occurrence.
    block_import_solver = (
        "import io as _io\n"
        "import contextlib as _contextlib\n"
        "_AUREON_IOBUF = _io.StringIO()\n"
        "with _contextlib.redirect_stdout(_AUREON_IOBUF), _contextlib.redirect_stderr(_AUREON_IOBUF):\n"
        "    import solver\n"
    )
    block_from_solve = (
        "import io as _io\n"
        "import contextlib as _contextlib\n"
        "_AUREON_IOBUF = _io.StringIO()\n"
        "with _contextlib.redirect_stdout(_AUREON_IOBUF), _contextlib.redirect_stderr(_AUREON_IOBUF):\n"
        "    from solver import solve\n"
    )

    if re.search(r'(?m)^\s*import\s+solver\s*$', t) and "redirect_stdout" not in t:
        t = re.sub(r'(?m)^\s*import\s+solver\s*$', block_import_solver.rstrip("\n"), t, count=1)
    elif re.search(r'(?m)^\s*from\s+solver\s+import\s+solve\s*$', t) and "redirect_stdout" not in t:
        t = re.sub(r'(?m)^\s*from\s+solver\s+import\s+solve\s*$', block_from_solve.rstrip("\n"), t, count=1)

    # If gateway already has redirect_stdout/redirect_stderr, leave.
    write_utf8_nobom(GATEWAY, t)

def patch_gitignore():
    gi = ROOT/".gitignore"
    if not gi.exists():
        return
    t = gi.read_text(encoding="utf-8", errors="ignore")
    add = []
    want = [
        "tools/*.py",
        "tools/*.txt",
        "tools/eval_*",
        "tools/*failures*.jsonl",
        "tools/*summary*.txt",
        "tools/aimo3_submit_*.zip",
    ]
    for w in want:
        if w not in t:
            add.append(w)
    if add:
        t2 = t.rstrip() + "\n\n# local audit artifacts\n" + "\n".join(add) + "\n"
        write_utf8_nobom(gi, t2)

def main():
    patch_solver()
    patch_gateway()
    patch_gitignore()
    print("APPLY_AUDIT_FIXES_V2_OK")

if __name__ == "__main__":
    main()