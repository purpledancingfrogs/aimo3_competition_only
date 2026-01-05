import re
from dataclasses import dataclass
from typing import Optional, List, Tuple

# Deterministic modular arithmetic micro-engine:
# - parses simple integer expressions with + - * ^ and parentheses
# - evaluates expression mod m with fast pow
# - handles common olympiad phrasings (remainder, last digit, congruences, CRT(2))

@dataclass
class Tok:
    k: str
    v: str

def _tok(expr: str) -> List[Tok]:
    s = expr.replace(" ", "")
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c.isdigit():
            j = i
            while j < len(s) and s[j].isdigit():
                j += 1
            out.append(Tok("num", s[i:j]))
            i = j
            continue
        if c in "+-*^()":
            out.append(Tok(c, c))
            i += 1
            continue
        # ignore any other chars (keep parser robust)
        i += 1
    return out

def _prec(op: str) -> int:
    if op == "^": return 3
    if op == "*": return 2
    if op in "+-": return 1
    return 0

def _right_assoc(op: str) -> bool:
    return op == "^"

def _to_rpn(tokens: List[Tok]) -> List[Tok]:
    out: List[Tok] = []
    st: List[Tok] = []
    prev = None
    for t in tokens:
        if t.k == "num":
            out.append(t); prev = t; continue
        if t.k in "+-*^":
            # unary minus -> treat as 0 - x
            if t.k == "-" and (prev is None or prev.k in "+-*^("):
                out.append(Tok("num","0"))
            while st and st[-1].k in "+-*^":
                top = st[-1].k
                if (_prec(top) > _prec(t.k)) or (_prec(top) == _prec(t.k) and not _right_assoc(t.k)):
                    out.append(st.pop())
                else:
                    break
            st.append(t); prev = t; continue
        if t.k == "(":
            st.append(t); prev = t; continue
        if t.k == ")":
            while st and st[-1].k != "(":
                out.append(st.pop())
            if st and st[-1].k == "(":
                st.pop()
            prev = t; continue
    while st:
        out.append(st.pop())
    return out

def eval_mod(expr: str, mod: int) -> Optional[int]:
    if mod <= 0:
        return None
    tokens = _tok(expr)
    if not tokens:
        return None
    rpn = _to_rpn(tokens)
    st: List[int] = []
    for t in rpn:
        if t.k == "num":
            st.append(int(t.v) % mod)
        elif t.k in "+-*^":
            if len(st) < 2:
                return None
            b = st.pop()
            a = st.pop()
            if t.k == "+":
                st.append((a + b) % mod)
            elif t.k == "-":
                st.append((a - b) % mod)
            elif t.k == "*":
                st.append((a * b) % mod)
            elif t.k == "^":
                # exponent must be an integer; we only support small/medium exponents already reduced mod?
                # use exact exponent by re-parsing the original token sequence segment isn't feasible in RPN;
                # but in our tokenization, exponents are integers; in RPN stack b already reduced mod -> not safe.
                # workaround: restrict: if exponent came from a literal num, it was reduced mod; detect and bail if mod is small?
                # Instead: if exponent token was literal, b equals literal%mod; not acceptable generally.
                # So: re-evaluate exponent in Z (no mod) for pure numeric exponent forms we parse via regex path.
                return None
        else:
            return None
    if len(st) != 1:
        return None
    return st[0] % mod

def pow_mod(a: int, e: int, m: int) -> int:
    return pow(a % m, e, m)

def crt2(a1: int, m1: int, a2: int, m2: int) -> Optional[int]:
    # x ≡ a1 (mod m1), x ≡ a2 (mod m2)
    # returns least nonnegative solution modulo lcm if coprime; else handles compatible case.
    import math
    g = math.gcd(m1, m2)
    if (a2 - a1) % g != 0:
        return None
    l = (m1 // g) * m2
    # reduce to coprime
    m1p = m1 // g
    m2p = m2 // g
    # find inv of m1p mod m2p
    def eg(a,b):
        if b==0: return (a,1,0)
        g,x1,y1 = eg(b, a%b)
        return (g, y1, x1 - (a//b)*y1)
    gg, x, _ = eg(m1p, m2p)
    if gg != 1:
        return None
    inv = x % m2p
    t = ((a2 - a1)//g) % m2p
    k = (t * inv) % m2p
    return (a1 + m1 * k) % l

def try_modular(s: str):
    """
    Deterministic modular handler.
    Targets:
      - "last digit of a^b"  -> a^b mod 10
      - "last two digits of a^b" -> mod 100
      - "remainder when a^b is divided by m" -> a^b mod m
      - "a mod m" / "a modulo m" -> a % m
    Returns int or None.
    """
    if not s:
        return None
    sl = s.lower()

    def _powmod(a: int, e: int, mod: int) -> int:
        a %= mod
        if mod <= 0:
            return None
        return pow(a, e, mod)

    # last digit / last two digits
    if "last digit" in sl:
        mm = re.search(r"(-?\d+)\s*\^\s*(\d+)", sl)
        if mm:
            a = int(mm.group(1)); e = int(mm.group(2))
            return int(_powmod(a, e, 10))

    if "last two digits" in sl:
        mm = re.search(r"(-?\d+)\s*\^\s*(\d+)", sl)
        if mm:
            a = int(mm.group(1)); e = int(mm.group(2))
            return int(_powmod(a, e, 100))

    # remainder when ... divided by ...
    if "remainder" in sl and "divided by" in sl:
        mmM = re.search(r"divided\s+by\s+(\d+)", sl)
        mmP = re.search(r"(-?\d+)\s*\^\s*(\d+)", sl)
        if mmM and mmP:
            mod = int(mmM.group(1))
            a = int(mmP.group(1)); e = int(mmP.group(2))
            return int(_powmod(a, e, mod))

    # explicit mod / modulo / modulus
    mm = re.search(r"(-?\d+)\s*(?:mod|modulo)\s*(\d+)", sl)
    if mm:
        a = int(mm.group(1)); mod = int(mm.group(2))
        if mod != 0:
            return int(a % mod)

    return None
