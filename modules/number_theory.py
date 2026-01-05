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

def try_modular(text: str) -> Optional[int]:
    s = (text or "").strip()
    sl = s.lower()

    # robust fallbacks (handles punctuation/cleaning variance)
    if "last digit" in sl:
        mm = re.search(r"(-?\d+)\s*\^\s*(\d+)", sl)
        if mm:
            a = int(mm.group(1)); e = int(mm.group(2))
            return pow_mod(a, e, 10)

    if "last two digits" in sl:
        mm = re.search(r"(-?\d+)\s*\^\s*(\d+)", sl)
        if mm:
            a = int(mm.group(1)); e = int(mm.group(2))
            return pow_mod(a, e, 100)

    if "remainder when" in sl and "divided by" in sl:
        mmM = re.search(r"divided\s+by\s+(\d+)", sl)
        mmP = re.search(r"(-?\d+)\s*\^\s*(\d+)", sl)
        if mmM and mmP:
            mod = int(mmM.group(1))
            a = int(mmP.group(1)); e = int(mmP.group(2))
            return pow_mod(a, e, mod)

    # last digit / last two digits
    m = re.search(r"last\s+digit\s+of\s+(-?\d+)\s*\^\s*(\d+)", sl)
    if m:
        a = int(m.group(1)); e = int(m.group(2))
        return pow_mod(a, e, 10)

    m = re.search(r"last\s+two\s+digits\s+of\s+(-?\d+)\s*\^\s*(\d+)", sl)
    if m:
        a = int(m.group(1)); e = int(m.group(2))
        return pow_mod(a, e, 100)

    # remainder when (expression) is divided by m
    m = re.search(r"remainder\s+when\s+(.+?)\s+is\s+divided\s+by\s+(\d+)", sl)
    if m:
        expr = m.group(1)
        mod = int(m.group(2))
        # fast path: single power a^e
        mm = re.fullmatch(r"\s*(-?\d+)\s*\^\s*(\d+)\s*", expr)
        if mm:
            a = int(mm.group(1)); e = int(mm.group(2))
            return pow_mod(a, e, mod)
        # allow a*b + c*d with powers
        # fallback: if expression contains only digits/operators/parens/spaces, try direct modular eval without ^
        if "^" not in expr:
            v = eval_mod(expr, mod)
            return v
        # limited: split on + and - at top-level for sums of powers like a^e + b^f
        parts = re.split(r"(?<!\^)\+", expr)
        if len(parts) <= 6:
            total = 0
            for part in parts:
                part = part.strip()
                mm2 = re.fullmatch(r"\s*(-?\d+)\s*\^\s*(\d+)\s*", part)
                if mm2:
                    total = (total + pow_mod(int(mm2.group(1)), int(mm2.group(2)), mod)) % mod
                else:
                    # try simple eval with no caret
                    if "^" in part:
                        return None
                    vv = eval_mod(part, mod)
                    if vv is None:
                        return None
                    total = (total + vv) % mod
            return total
        return None

    # congruence: x ≡ a (mod m) and maybe second congruence, ask for least positive x
    if ("mod" in sl or "modulo" in sl or "congruent" in sl) and ("least" in sl or "smallest" in sl):
        # extract up to two congruences of form x ≡ a (mod m)
        cons = re.findall(r"x\s*≡\s*(-?\d+)\s*\(mod\s*(\d+)\)", s)
        if len(cons) >= 1:
            a1, m1 = int(cons[0][0]), int(cons[0][1])
            if len(cons) >= 2:
                a2, m2 = int(cons[1][0]), int(cons[1][1])
                x = crt2(a1 % m1, m1, a2 % m2, m2)
                if x is None:
                    return None
                return x if x != 0 else (m1 * m2)  # least positive
            x = a1 % m1
            return x if x != 0 else m1

    return None
