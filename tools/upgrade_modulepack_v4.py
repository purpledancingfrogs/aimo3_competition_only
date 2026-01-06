import re, math

PATH="solver.py"

def _append_patch(src: str) -> str:
    if "MPV4_PATCH_BEGIN" in src:
        print("ALREADY_PATCHED")
        return src

    patch = r'''

# === MPV4_PATCH_BEGIN ===
import re as _re
import math as _math

# fast guards
_mpv4_allowed = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+-*/^()= \n\r\t.,:;_[]{}<>≡∈|&!?'\"")
def _mpv4_chars_ok(s: str) -> bool:
    # allow common unicode symbols we normalize away
    for ch in s:
        if ch in _mpv4_allowed: 
            continue
        o = ord(ch)
        if o in (0x2261, 0x2260, 0x00D7, 0x2212, 0x03C0):  # ≡ ≠ × − π
            continue
        # allow basic unicode spaces
        if ch.isspace():
            continue
        return False
    return True

def _mpv4_norm(s: str) -> str:
    s = s.replace("×","*").replace("−","-").replace("^","**")
    # keep "mod" readable
    return s

_mpv4_re_fact_digitsum = _re.compile(r"(?:sum of digits of)\s+(\d{1,6})\s*!\s*", _re.I)
_mpv4_re_powmod_1 = _re.compile(r"\b(\d{1,9})\s*(?:\*\*|\^)\s*(\d{1,9})\s*(?:mod|%|modulo)\s*(\d{1,9})\b", _re.I)
_mpv4_re_powmod_2 = _re.compile(r"\b(?:powmod|power mod|compute)\s+(\d{1,9})\s*(?:\*\*|\^)\s*(\d{1,9})\s*(?:mod|%|modulo)\s*(\d{1,9})\b", _re.I)
_mpv4_re_mod_simple = _re.compile(r"\b(\d{1,18})\s*(?:mod|%|modulo)\s*(\d{1,9})\b", _re.I)

_mpv4_re_cong_1 = _re.compile(r"(?:≡|=)\s*(-?\d{1,18})\s*\(\s*mod\s*(\d{1,18})\s*\)", _re.I)
_mpv4_re_cong_2 = _re.compile(r"(?:mod\s*(\d{1,18})\s*:\s*)(-?\d{1,18})", _re.I)

def _egcd(a:int,b:int):
    x0,y0,x1,y1=1,0,0,1
    while b:
        q=a//b
        a,b=b,a-q*b
        x0,x1=x1,x0-q*x1
        y0,y1=y1,y0-q*y1
    return a,x0,y0

def _crt_pair(a1:int,m1:int,a2:int,m2:int):
    # solve x=a1 mod m1, x=a2 mod m2 (possibly non-coprime)
    g,p,q=_egcd(m1,m2)
    if (a2-a1)%g!=0:
        return None
    l = (m1//g)*m2
    t = ((a2-a1)//g) * p
    x = (a1 + m1*t) % l
    return x, l

def _crt_all(pairs):
    x,m = pairs[0]
    x%=m
    for a2,m2 in pairs[1:]:
        a2%=m2
        r=_crt_pair(x,m,a2,m2)
        if r is None:
            return None
        x,m=r
    return x%m

def _mpv4_try_sympy_system(text: str):
    try:
        import sympy as sp
    except Exception:
        return None

    if not _mpv4_chars_ok(text):
        return None

    t = _mpv4_norm(text)

    # collect equation-like parts
    eqs=[]
    # split into candidate lines/chunks
    chunks = re.split(r"[\n;]+", t)
    for ch in chunks:
        if "=" not in ch:
            continue
        # keep only simple equation characters
        if not re.fullmatch(r"[0-9a-zA-Z+\-*/().=\s]+", ch):
            continue
        # one '=' only
        if ch.count("=")!=1:
            continue
        L,R = ch.split("=")
        L=L.strip(); R=R.strip()
        if not L or not R:
            continue
        eqs.append((L,R))
    if not eqs:
        return None

    # variables: prefer x,y,z,a,b,c
    vars=set()
    for L,R in eqs:
        for v in ("x","y","z","a","b","c","n","m","k"):
            if re.search(rf"\b{v}\b", L) or re.search(rf"\b{v}\b", R):
                vars.add(v)
    if not vars or len(vars)>3:
        return None

    syms = {v: sp.Symbol(v, integer=True) for v in vars}
    equations=[]
    for L,R in eqs[:5]:
        try:
            l = sp.sympify(L, locals=syms)
            r = sp.sympify(R, locals=syms)
            equations.append(sp.Eq(l,r))
        except Exception:
            return None

    try:
        sol = sp.linsolve(equations, [syms[v] for v in sorted(vars)])
    except Exception:
        return None
    if not sol:
        return None
    sol_list=list(sol)
    if not sol_list:
        return None
    tup=sol_list[0]
    if len(tup)!=len(vars):
        return None

    assign = {sorted(vars)[i]: tup[i] for i in range(len(vars))}

    # if question asks for sum/expression like x+y or x+y+z
    m = re.search(r"\b(?:find|compute)\b[^.\n]*\b([xyzabc](?:\s*[\+\-]\s*[xyzabc]){1,4})\b", t, re.I)
    if m:
        expr_str = m.group(1).replace(" ", "")
        try:
            expr = sp.sympify(expr_str, locals=syms)
            val = expr.subs({syms[k]: assign[k] for k in assign})
            val = sp.nsimplify(val)
            if val.is_integer:
                return str(int(val))
        except Exception:
            pass

    # else if single variable requested
    m2 = re.search(r"\b(?:find|solve for)\b[^.\n]*\b([xyzabc])\b", t, re.I)
    if m2:
        v=m2.group(1)
        if v in assign:
            val = sp.nsimplify(assign[v])
            if val.is_integer:
                return str(int(val))

    return None

def _mpv4_solve(text: str):
    if not text:
        return None
    t = text.strip()
    if not t:
        return None
    if len(t) > 20000:
        return None

    # factorial digit sum
    m = _mpv4_re_fact_digitsum.search(t)
    if m:
        n = int(m.group(1))
        if 0 <= n <= 50000:  # safe big-int bound
            f = _math.factorial(n)
            return str(sum((ord(c)-48) for c in str(f)))

    # powmod
    for rr in (_mpv4_re_powmod_1, _mpv4_re_powmod_2):
        m = rr.search(t)
        if m:
            a=int(m.group(1)); b=int(m.group(2)); mod=int(m.group(3))
            if mod != 0:
                return str(pow(a,b,mod))

    # simple mod
    m = _mpv4_re_mod_simple.search(t)
    if m:
        a=int(m.group(1)); mod=int(m.group(2))
        if mod != 0:
            return str(a % mod)

    # CRT: grab congruences
    pairs=[]
    for a,mn in _mpv4_re_cong_1.findall(t):
        aa=int(a); mm=int(mn)
        if mm != 0:
            pairs.append((aa, abs(mm)))
    if len(pairs) < 2:
        # alt "mod m: a" format
        for mn,a in _mpv4_re_cong_2.findall(t):
            aa=int(a); mm=int(mn)
            if mm != 0:
                pairs.append((aa, abs(mm)))

    if len(pairs) >= 2 and len(pairs) <= 6:
        r = _crt_all(pairs)
        if r is not None:
            return str(int(r))

    # sympy bounded system/equation solver (linear-ish)
    r = _mpv4_try_sympy_system(t)
    if r is not None:
        return r

    return None

# monkeypatch Solver.solve to try MPV4 first, then original
try:
    _MPV4_SOLVE0 = Solver.solve
    def _mpv4_solve_wrap(self, text):
        ans = _mpv4_solve(text)
        if ans is not None:
            return ans
        return _MPV4_SOLVE0(self, text)
    Solver.solve = _mpv4_solve_wrap
except Exception:
    pass
# === MPV4_PATCH_END ===
'''
    return src + patch

def main():
    with open(PATH, "r", encoding="utf-8") as f:
        src = f.read()
    out = _append_patch(src)
    with open(PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    print("PATCHED_MPV4")

if __name__ == "__main__":
    main()
