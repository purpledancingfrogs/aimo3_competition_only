import re, math, textwrap

PATH="solver.py"

def _append_patch(src: str) -> str:
    if "MPV8_PATCH_BEGIN" in src:
        print("ALREADY_PATCHED_MPV8")
        return src

    patch = r'''

# === MPV8_PATCH_BEGIN ===
import re as _re
import math as _math

# ---------- helpers ----------
def _mpv8_norm(s: str) -> str:
    if s is None:
        return ""
    s = s.replace("\u00a0"," ")
    s = s.replace("×","*").replace("·","*").replace("−","-").replace("^","**")
    s = s.replace("“",'"').replace("”",'"').replace("’","'").replace("‘","'")
    return s

def _mpv8_int(s):
    try:
        if isinstance(s, bool): return None
        if s is None: return None
        if hasattr(s, "is_integer") and s.is_integer is True:
            return int(s)
        if isinstance(s, (int,)): return int(s)
        if isinstance(s, (float,)):
            if abs(s-round(s))<1e-12: return int(round(s))
            return None
        return int(str(s).strip())
    except Exception:
        return None

# ---------- factorial digit sum ----------
_mpv8_re_fact_digitsum = _re.compile(r"(?:sum\s+of\s+digits\s+of)\s+(\d{1,7})\s*!\s*(?:[)\].,:;\"'\s]|$)", _re.I)

def _mpv8_fact_digitsum(n: int):
    if n < 0 or n > 20000:
        return None
    f = _math.factorial(n)
    return str(sum((ord(c)-48) for c in str(f)))

# ---------- gcd / lcm ----------
_mpv8_re_gcd = _re.compile(r"\bgcd\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)\b", _re.I)
_mpv8_re_lcm = _re.compile(r"\blcm\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)\b", _re.I)

def _mpv8_gcd(a,b): return _math.gcd(int(a), int(b))
def _mpv8_lcm(a,b):
    a=int(a); b=int(b)
    if a==0 or b==0: return 0
    return abs(a//_math.gcd(a,b)*b)

# ---------- powmod / mod ----------
_mpv8_re_mod = _re.compile(r"\b(-?\d+)\s*(?:mod|%|modulo)\s*(\d+)\b", _re.I)
_mpv8_re_powmod = _re.compile(r"\b(-?\d+)\s*(?:\^|\*\*)\s*(\d+)\s*(?:mod|modulo)\s*(\d+)\b", _re.I)
_mpv8_re_powmod2 = _re.compile(r"\b(?:compute|find)\s+(-?\d+)\s*(?:\^|\*\*)\s*(\d+)\s*(?:mod|modulo)\s*(\d+)\b", _re.I)

# ---------- linear equation ax+b=c ----------
_mpv8_re_lin1 = _re.compile(r"^\s*([+-]?\d+)\s*\*\s*([a-z])\s*([+-]\s*\d+)\s*=\s*([+-]?\d+)\s*$", _re.I)
_mpv8_re_lin2 = _re.compile(r"^\s*([+-]?\d+)\s*([a-z])\s*([+-]\s*\d+)\s*=\s*([+-]?\d+)\s*$", _re.I)

# ---------- system of 2 linear equations in x,y (robust, no sympy needed) ----------
# handles: "7*x + 6*y = 295 5*x + 7*y = 189" and also newline/semicolon separated
_mpv8_eq_find = _re.compile(r"([0-9a-zA-Z+\-*/().,\s]{1,200})=([0-9a-zA-Z+\-*/().,\s]{1,200})")

def _mpv8_parse_linear_expr_xy(expr: str):
    # returns (ax, ay, c) for expression ax*x + ay*y + c (no other vars)
    # supports implicit mult: 7x, -3y, 2*x, 4*y
    e = _mpv8_norm(expr)
    e = e.replace(" ", "")
    # normalize unary +/-
    if not e:
        return None
    # reject other letters besides x,y
    if _re.search(r"[a-wzA-WZ]", e):
        return None

    # tokenize into signed terms
    terms=[]
    i=0
    sign=1
    if e[0] == '+':
        i=1
    elif e[0] == '-':
        sign=-1; i=1
    start=i
    for j in range(i, len(e)):
        if e[j] in "+-":
            terms.append((sign, e[start:j]))
            sign = 1 if e[j] == '+' else -1
            start = j+1
    terms.append((sign, e[start:]))

    ax=0; ay=0; c=0
    for sg, t in terms:
        if t=="":
            return None
        # strip leading '*'
        if t.startswith("*"):
            t=t[1:]
        # x or y term?
        m = _re.fullmatch(r"(\d+)?\*?x", t, _re.I)
        if m:
            k = int(m.group(1)) if m.group(1) else 1
            ax += sg*k
            continue
        m = _re.fullmatch(r"(\d+)?\*?y", t, _re.I)
        if m:
            k = int(m.group(1)) if m.group(1) else 1
            ay += sg*k
            continue
        # constant
        if _re.fullmatch(r"\d+", t):
            c += sg*int(t)
            continue
        # allow parenthesized integer
        m = _re.fullmatch(r"\(([-+]?\d+)\)", t)
        if m:
            c += sg*int(m.group(1))
            continue
        return None
    return ax, ay, c

def _mpv8_solve_2x2_xy(eq1L, eq1R, eq2L, eq2R):
    p1=_mpv8_parse_linear_expr_xy(eq1L)
    q1=_mpv8_parse_linear_expr_xy(eq1R)
    p2=_mpv8_parse_linear_expr_xy(eq2L)
    q2=_mpv8_parse_linear_expr_xy(eq2R)
    if not (p1 and q1 and p2 and q2):
        return None
    a1,b1,c1 = p1
    ar1,br1,cr1 = q1
    a2,b2,c2 = p2
    ar2,br2,cr2 = q2
    # move to left: (a1-ar1)x + (b1-br1)y + (c1-cr1)=0 => (a)x+(b)y = d
    A1 = a1 - ar1
    B1 = b1 - br1
    D1 = cr1 - c1
    A2 = a2 - ar2
    B2 = b2 - br2
    D2 = cr2 - c2
    det = A1*B2 - A2*B1
    if det == 0:
        return None
    # Cramer's rule
    x_num = D1*B2 - D2*B1
    y_num = A1*D2 - A2*D1
    if x_num % det != 0 or y_num % det != 0:
        return None
    x = x_num // det
    y = y_num // det
    return x, y

def _mpv8_try_linear_system(text: str):
    t=_mpv8_norm(text)
    # extract equations
    eqs=[]
    for m in _mpv8_eq_find.finditer(t):
        L=m.group(1).strip()
        R=m.group(2).strip()
        if not L or not R: 
            continue
        # prune extremely long segments
        if len(L)>200 or len(R)>200:
            continue
        # must mention x or y
        if ("x" not in L.lower() and "y" not in L.lower() and "x" not in R.lower() and "y" not in R.lower()):
            continue
        # allow only safe chars
        if not _re.fullmatch(r"[0-9a-zA-Z+\-*/().,\s]+", L):
            continue
        if not _re.fullmatch(r"[0-9a-zA-Z+\-*/().,\s]+", R):
            continue
        eqs.append((L,R))
    if len(eqs) < 2:
        return None
    # take first 2 equations containing x/y
    (L1,R1),(L2,R2)=eqs[0],eqs[1]
    sol=_mpv8_solve_2x2_xy(L1,R1,L2,R2)
    if sol is None:
        return None
    x,y=sol
    # requested x+y
    if _re.search(r"\bx\s*\+\s*y\b", t, _re.I) or _re.search(r"\breturn\s+x\s*\+\s*y\b", t, _re.I):
        return str(x+y)
    # else return x if asked, y if asked
    if _re.search(r"\bsolve\s+for\s+x\b|\bfind\s+x\b", t, _re.I):
        return str(x)
    if _re.search(r"\bsolve\s+for\s+y\b|\bfind\s+y\b", t, _re.I):
        return str(y)
    # default x+y (common in selfplay)
    return str(x+y)

# ---------- digitsum (non-factorial) ----------
_mpv8_re_digitsum = _re.compile(r"\b(?:sum\s+of\s+digits\s+of)\s+(\d{1,200})\b", _re.I)

def _mpv8_digitsum(snum: str):
    snum = snum.strip()
    if len(snum) > 200:
        return None
    if not _re.fullmatch(r"\d+", snum):
        return None
    return str(sum(ord(c)-48 for c in snum))

# ---------- top-level mpv8 solve ----------
def _mpv8_solve(text: str):
    if not text:
        return None
    t = text.strip()
    if not t:
        return None
    if len(t) > 50000:
        return None

    # factorial digit sum
    m=_mpv8_re_fact_digitsum.search(t)
    if m:
        n=int(m.group(1))
        r=_mpv8_fact_digitsum(n)
        if r is not None:
            return r

    # system x,y (Cramer's)
    r=_mpv8_try_linear_system(t)
    if r is not None:
        return r

    # powmod
    m=_mpv8_re_powmod.search(_mpv8_norm(t)) or _mpv8_re_powmod2.search(_mpv8_norm(t))
    if m:
        a=int(m.group(1)); b=int(m.group(2)); mod=int(m.group(3))
        if mod>0 and b>=0 and b<=10**7:
            return str(pow(a, b, mod))

    # mod
    m=_mpv8_re_mod.search(_mpv8_norm(t))
    if m:
        a=int(m.group(1)); mod=int(m.group(2))
        if mod>0:
            return str(a % mod)

    # gcd/lcm
    m=_mpv8_re_gcd.search(t)
    if m:
        return str(_mpv8_gcd(m.group(1), m.group(2)))
    m=_mpv8_re_lcm.search(t)
    if m:
        return str(_mpv8_lcm(m.group(1), m.group(2)))

    # digitsum of integer literal
    m=_mpv8_re_digitsum.search(t)
    if m:
        r=_mpv8_digitsum(m.group(1))
        if r is not None:
            return r

    # single-variable linear (ax + b = c)
    tt=_mpv8_norm(t).replace(" ", "")
    m=_mpv8_re_lin1.match(tt) or _mpv8_re_lin2.match(tt)
    if m:
        a=int(m.group(1)); v=m.group(2); b=int(m.group(3).replace(" ","")); c=int(m.group(4))
        if a!=0:
            num=c-b
            if num % a == 0:
                return str(num//a)

    return None

try:
    _MPV8_SOLVE0 = Solver.solve
    def _mpv8_wrap(self, text):
        ans=_mpv8_solve(text)
        if ans is not None:
            return ans
        return _MPV8_SOLVE0(self, text)
    Solver.solve=_mpv8_wrap
except Exception:
    pass
# === MPV8_PATCH_END ===

'''
    return src + patch

def main():
    with open(PATH,"r",encoding="utf-8") as f:
        src=f.read()
    out=_append_patch(src)
    with open(PATH,"w",encoding="utf-8",newline="\n") as f:
        f.write(out)
    print("PATCHED_MPV8")

if __name__=="__main__":
    main()
