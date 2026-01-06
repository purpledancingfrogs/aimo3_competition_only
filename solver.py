import re, math

_INT_RE = re.compile(r"-?\d+")

def _norm(s: str) -> str:
    s = s.replace("\r\n", "\n")

    # latex tokens -> plain
    s = re.sub(r"\\left|\\right", "", s)
    s = s.replace("\\equiv", "≡").replace("\\cong", "≡")
    s = s.replace("\\bmod", "mod").replace("\\mod", "mod")

    # \pmod{...} -> (mod ...)
    s = re.sub(r"\\pmod\s*\{\s*([^}]+)\s*\}", r"(mod \1)", s)

    # remove $ and braces; convert ^{123} -> ^123
    s = s.replace("$", "")
    s = re.sub(r"\^\s*\{\s*(-?\d+)\s*\}", r"^\1", s)
    s = s.replace("{", "").replace("}", "")

    # unicode minus and times
    s = s.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-").replace("−", "-")
    s = s.replace("\u00d7", "*").replace("\u00b7", "*")

    return s

def _safe_mod(m: int):
    if m == 0: return None
    return abs(int(m))

def _inv_mod(a: int, m: int):
    a %= m
    if a == 0: return None
    if math.gcd(a, m) != 1: return None
    try:
        return pow(a, -1, m)
    except Exception:
        # egcd fallback
        def egcd(x, y):
            if y == 0: return (x, 1, 0)
            g, x1, y1 = egcd(y, x % y)
            return (g, y1, x1 - (x // y) * y1)
        g, x, _ = egcd(a, m)
        if g != 1: return None
        return x % m

def _first_int(s: str):
    m = _INT_RE.search(s)
    return int(m.group(0)) if m else None

# ---------------- handlers ----------------

# system_sum: 2x2 linear system, return x+y
_EQ_RE = re.compile(r"(?P<lhs>[^\n=]{1,180}?[xy][^\n=]{0,180}?)\s*=\s*(?P<rhs>-?\d+)\b", re.IGNORECASE)

def _parse_lhs(lhs: str):
    lhs = _norm(lhs).replace(" ", "")
    if not lhs: return None
    if re.search(r"[^0-9xyXY+\-*]", lhs): return None
    if lhs[0] not in "+-": lhs = "+" + lhs
    terms = re.findall(r"[+-][^+-]+", lhs)
    a=b=k=0
    for t in terms:
        sign = -1 if t[0] == "-" else 1
        body = t[1:]
        low = body.lower()
        if "x" in low or "y" in low:
            var = "x" if "x" in low else "y"
            coeff_str = low.replace(var, "").replace("*", "")
            if coeff_str == "":
                coeff = 1
            else:
                if not re.fullmatch(r"\d+", coeff_str): return None
                coeff = int(coeff_str)
            coeff *= sign
            if var == "x": a += coeff
            else: b += coeff
        else:
            if not re.fullmatch(r"\d+", body): return None
            k += sign * int(body)
    return a,b,k

def _cramer(a1,b1,c1,a2,b2,c2):
    D = a1*b2 - a2*b1
    if D == 0: return None
    x_num = c1*b2 - c2*b1
    y_num = a1*c2 - a2*c1
    if x_num % D != 0 or y_num % D != 0: return None
    return x_num//D, y_num//D

def handle_system_sum(s: str):
    t = s.lower()
    if "system" not in t: return None
    ms = list(_EQ_RE.finditer(s))
    eqs=[]
    for m in ms:
        lhs = m.group("lhs")
        rhs = int(m.group("rhs"))
        parsed = _parse_lhs(lhs)
        if parsed is None: continue
        a,b,k = parsed
        c = rhs - k
        eqs.append((a,b,c))
        if len(eqs) == 2: break
    if len(eqs) != 2: return None
    (a1,b1,c1),(a2,b2,c2)=eqs
    sol = _cramer(a1,b1,c1,a2,b2,c2)
    if sol is None: return None
    x,y = sol
    return str(x+y)

# nCk
_NCK1 = re.compile(r"\b(?:c|choose)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", re.IGNORECASE)
_NCK2 = re.compile(r"\bC\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)")

def handle_nCk(s: str):
    m = _NCK1.search(s) or _NCK2.search(s)
    if not m: return None
    n = int(m.group(1)); k = int(m.group(2))
    if k < 0 or n < 0 or k > n: return None
    if n > 200000: return None
    return str(math.comb(n,k))

# gcd/lcm
_GCD = re.compile(r"gcd\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)", re.IGNORECASE)
_LCM = re.compile(r"lcm\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)", re.IGNORECASE)

def handle_gcd(s: str):
    m=_GCD.search(s)
    if not m: return None
    return str(math.gcd(int(m.group(1)), int(m.group(2))))

def handle_lcm(s: str):
    m=_LCM.search(s)
    if not m: return None
    a=int(m.group(1)); b=int(m.group(2))
    if a == 0 or b == 0: return "0"
    g=math.gcd(a,b)
    return str(abs(a//g*b))

# linear ax+b=c
_LIN = re.compile(r"([^\n=]{1,220}?x[^\n=]{0,220}?)\s*=\s*(-?\d+)\b", re.IGNORECASE)

def handle_linear(s: str):
    m=_LIN.search(s)
    if not m: return None
    lhs=m.group(1).replace(" ","")
    rhs=int(m.group(2))
    if lhs.lower().count("x") != 1: return None
    if re.search(r"[^0-9xX+\-*]", lhs): return None
    if lhs[0] not in "+-": lhs="+"+lhs
    terms=re.findall(r"[+-][^+-]+", lhs)
    a=0; k=0
    for term in terms:
        sign=-1 if term[0]=="-" else 1
        body=term[1:]
        low=body.lower()
        if "x" in low:
            coeff_str=low.replace("x","").replace("*","")
            if coeff_str=="": coeff=1
            else:
                if not re.fullmatch(r"\d+", coeff_str): return None
                coeff=int(coeff_str)
            a += sign*coeff
        else:
            if not re.fullmatch(r"\d+", body): return None
            k += sign*int(body)
    if a == 0: return None
    num = rhs - k
    if num % a != 0: return None
    return str(num//a)

# powmod: a^e mod m  (handles latex ^{e} via _norm)
_POW = re.compile(r"(-?\d+)\s*(?:\^|\*\*)\s*(-?\d+)\s*mod\s*(-?\d+)", re.IGNORECASE)

def handle_powmod(s: str):
    if "mod" not in s.lower(): return None
    m=_POW.search(s)
    if not m: return None
    a=int(m.group(1)); e=int(m.group(2)); mod0=int(m.group(3))
    mod=_safe_mod(mod0)
    if mod is None or e < 0: return None
    if mod == 1: return "0"
    try:
        return str(pow(a,e,mod))
    except Exception:
        return None

# CRT: x ≡ a (mod m) and x ≡ b (mod n)
# also accept "x ? a (mod m)" from prompt encoding
_CONG = re.compile(r"x\s*(?:≡|=|\?)\s*(-?\d+)\s*\(\s*mod\s*(-?\d+)\s*\)", re.IGNORECASE)

def _crt_pair(a1,m1,a2,m2):
    g=math.gcd(m1,m2)
    if (a2-a1) % g != 0: return None
    l=(m1//g)*m2
    m1g=m1//g
    m2g=m2//g
    rhs=(a2-a1)//g
    if m2g == 1:
        return (a1 % l, l)
    inv=_inv_mod(m1g % m2g, m2g)
    if inv is None: return None
    t=(rhs % m2g) * inv % m2g
    a=(a1 + m1*t) % l
    return a,l

def handle_crt(s: str):
    if "mod" not in s.lower() and "≡" not in s and "?" not in s: return None
    congr=[]
    for a_s, m_s in _CONG.findall(s):
        mi0=int(m_s)
        mi=_safe_mod(mi0)
        if mi is None: return None
        if mi == 1: 
            continue
        ai=int(a_s) % mi
        congr.append((ai,mi))
    if len(congr) < 2: return None
    a,m=congr[0]
    for ai,mi in congr[1:]:
        res=_crt_pair(a,m,ai,mi)
        if res is None: return None
        a,m=res
    return str(a % m)

class Solver:
    def solve(self, prompt: str) -> str:
        s=_norm(prompt)
        try:
            for fn in (
                handle_system_sum,
                handle_nCk,
                handle_crt,
                handle_powmod,
                handle_gcd,
                handle_lcm,
                handle_linear,
            ):
                out=fn(s)
                if out is not None:
                    out=out.strip()
                    return out if re.fullmatch(r"-?\d+", out) else "0"
        except Exception:
            return "0"
        v=_first_int(s)
        return str(v if v is not None else 0)

if __name__ == "__main__":
    import sys
    ans=Solver().solve(sys.stdin.read()).strip()
    if not re.fullmatch(r"-?\d+", ans): ans="0"
    sys.stdout.write(ans)
