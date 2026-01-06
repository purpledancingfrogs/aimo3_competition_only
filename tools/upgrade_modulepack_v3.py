# tools/upgrade_modulepack_v3.py
from __future__ import annotations
import io, os, re, sys, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOLVER = ROOT / "solver.py"

MARK = "# === MODULEPACK_V3_START ==="

MPV3_CODE = r'''
# === MODULEPACK_V3_START ===
import re as _mpv3_re
import math as _mpv3_math

_mpv3_pat_powmod = _mpv3_re.compile(r"(?:remainder\s+when|mod(?:ulo)?|mod)\s*(?:\(?\s*)?(\d+)\s*(?:\^|\*\*)\s*(\d+)\s*(?:\)?\s*)?(?:is\s*)?(?:divided\s+by|mod(?:ulo)?|mod)\s*(\d+)", _mpv3_re.I)
_mpv3_pat_powmod2 = _mpv3_re.compile(r"(\d+)\s*(?:\^|\*\*)\s*(\d+)\s*(?:mod|modulo)\s*(\d+)", _mpv3_re.I)
_mpv3_pat_gcd = _mpv3_re.compile(r"\bgcd\b[^0-9]*(\d+)[^0-9]+(\d+)", _mpv3_re.I)
_mpv3_pat_lcm = _mpv3_re.compile(r"\blcm\b[^0-9]*(\d+)[^0-9]+(\d+)", _mpv3_re.I)
_mpv3_pat_comb = _mpv3_re.compile(r"(?:\bC\s*\(|\bchoose\b|\bcombination(?:s)?\b)[^0-9]*(\d+)[^0-9]+(\d+)", _mpv3_re.I)
_mpv3_pat_fact = _mpv3_re.compile(r"\b(\d+)\s*!\b")
_mpv3_pat_digitsum = _mpv3_re.compile(r"(?:sum\s+of\s+digits\s+of)\s+(\d+)", _mpv3_re.I)

def _mpv3_norm(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    s = s.replace("\u2212", "-").replace("\u2013","-").replace("\u2014","-")
    s = s.replace("\u00d7","*").replace("\u00f7","/")
    s = s.replace("\u2009"," ").replace("\u00a0"," ")
    return s.strip()

def _mpv3_safe_int(x):
    try:
        return int(x)
    except Exception:
        return None

def _mpv3_nCk(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    k = min(k, n-k)
    num = 1
    den = 1
    for i in range(1, k+1):
        num *= (n - (k - i))
        den *= i
    return num // den

def _mpv3_try(s: str):
    s = _mpv3_norm(s)

    m = _mpv3_pat_powmod.search(s) or _mpv3_pat_powmod2.search(s)
    if m:
        a = _mpv3_safe_int(m.group(1)); b = _mpv3_safe_int(m.group(2)); mod = _mpv3_safe_int(m.group(3))
        if a is not None and b is not None and mod is not None and mod != 0:
            return pow(a, b, mod)

    m = _mpv3_pat_gcd.search(s)
    if m:
        a = _mpv3_safe_int(m.group(1)); b = _mpv3_safe_int(m.group(2))
        if a is not None and b is not None:
            return _mpv3_math.gcd(a, b)

    m = _mpv3_pat_lcm.search(s)
    if m:
        a = _mpv3_safe_int(m.group(1)); b = _mpv3_safe_int(m.group(2))
        if a is not None and b is not None:
            g = _mpv3_math.gcd(a, b)
            if g != 0:
                return abs(a // g * b)

    m = _mpv3_pat_digitsum.search(s)
    if m:
        n = m.group(1)
        return sum(int(ch) for ch in n)

    # direct "n!" for small n
    m = _mpv3_pat_fact.search(s)
    if m:
        n = _mpv3_safe_int(m.group(1))
        if n is not None and 0 <= n <= 2000:
            return _mpv3_math.factorial(n)

    # combinations
    m = _mpv3_pat_comb.search(s)
    if m:
        n = _mpv3_safe_int(m.group(1)); k = _mpv3_safe_int(m.group(2))
        if n is not None and k is not None and 0 <= n <= 200000 and 0 <= k <= 200000:
            return _mpv3_nCk(n, k)

    return None

def _mpv3_install():
    try:
        Solver
    except Exception:
        return
    if getattr(Solver, "_mpv3_installed", False):
        return
    Solver._mpv3_installed = True
    Solver._solve_orig = Solver.solve
    def _solve_v3(self, text):
        try:
            ans = _mpv3_try(text)
            if ans is not None:
                return str(int(ans))
        except Exception:
            pass
        out = self._solve_orig(text)
        try:
            return str(int(out)).strip()
        except Exception:
            return str(out).strip()
    Solver.solve = _solve_v3

_mpv3_install()
# === MODULEPACK_V3_END ===
'''

def main():
    src = SOLVER.read_text(encoding="utf-8")
    if MARK in src:
        print("ALREADY_PATCHED")
        return
    patched = src.rstrip() + "\n\n" + MPV3_CODE + "\n"
    SOLVER.write_text(patched, encoding="utf-8")
    print("PATCHED_V3")

if __name__ == "__main__":
    main()
