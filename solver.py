# solver.py
import re
import math
from typing import Optional, Tuple, List

_INT_RE = re.compile(r"-?\d+")
_EQ_RE = re.compile(
    r"(?P<lhs>[^\r\n=]{1,160}?[xy][^\r\n=]{0,160}?)\s*=\s*(?P<rhs>-?\d+)\b",
    re.IGNORECASE,
)
_CONG_RE = re.compile(
    r"x\s*(?:≡|=)\s*(-?\d+)\s*\(\s*mod\s*(-?\d+)\s*\)",
    re.IGNORECASE,
)
_POWMOD_RE = re.compile(
    r"(-?\d+)\s*(?:\^|\*\*)\s*(-?\d+)\s*mod\s*(-?\d+)",
    re.IGNORECASE,
)
_GCD_RE = re.compile(r"gcd\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)", re.IGNORECASE)
_LCM_RE = re.compile(r"lcm\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)", re.IGNORECASE)
_NCK_RE_1 = re.compile(r"\b(?:c|choose)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", re.IGNORECASE)
_NCK_RE_2 = re.compile(r"\bC\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)")

def _norm(s: str) -> str:
    s = s.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
    s = s.replace("\u00d7", "*").replace("\u00b7", "*")
    s = s.replace("−", "-")
    return s

def _first_int(s: str) -> Optional[int]:
    m = _INT_RE.search(s)
    return int(m.group(0)) if m else None

def _safe_mod(m: int) -> Optional[int]:
    if m == 0:
        return None
    return abs(int(m))

def _norm_residue(a: int, m: int) -> int:
    return a % m

def _egcd(a: int, b: int) -> Tuple[int, int, int]:
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = _egcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)

def _inv_mod(a: int, m: int) -> Optional[int]:
    a %= m
    if a == 0:
        return None
    if math.gcd(a, m) != 1:
        return None
    try:
        return pow(a, -1, m)
    except Exception:
        g, x, _ = _egcd(a, m)
        if g != 1:
            return None
        return x % m

def _parse_lhs_ax_by_const(lhs: str) -> Optional[Tuple[int, int, int]]:
    lhs = _norm(lhs).replace(" ", "")
    if not lhs:
        return None
    if re.search(r"[^0-9xyXY+\-*]", lhs):
        return None
    if lhs[0] not in "+-":
        lhs = "+" + lhs
    terms = re.findall(r"[+-][^+-]+", lhs)
    a = b = k = 0
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
                if not re.fullmatch(r"\d+", coeff_str):
                    return None
                coeff = int(coeff_str)
            coeff *= sign
            if var == "x":
                a += coeff
            else:
                b += coeff
        else:
            if not re.fullmatch(r"\d+", body):
                return None
            k += sign * int(body)
    return a, b, k

def _solve_2x2_cramer(a1: int, b1: int, c1: int, a2: int, b2: int, c2: int) -> Optional[Tuple[int, int]]:
    D = a1 * b2 - a2 * b1
    if D == 0:
        return None
    x_num = c1 * b2 - c2 * b1
    y_num = a1 * c2 - a2 * c1
    if x_num % D != 0 or y_num % D != 0:
        return None
    return x_num // D, y_num // D

def _extract_two_xy_equations(text: str) -> Optional[List[Tuple[int, int, int]]]:
    text = _norm(text)
    matches = list(_EQ_RE.finditer(text))
    eqs: List[Tuple[int, int, int]] = []
    for m in matches:
        lhs = m.group("lhs")
        rhs = int(m.group("rhs"))
        parsed = _parse_lhs_ax_by_const(lhs)
        if parsed is None:
            continue
        a, b, k = parsed
        c = rhs - k
        eqs.append((a, b, c))
        if len(eqs) == 2:
            return eqs
    return None

def _handle_system_sum(text: str) -> Optional[str]:
    t = text.lower()
    if "system" not in t:
        return None
    if t.count("=") < 2:
        return None
    eqs = _extract_two_xy_equations(text)
    if not eqs or len(eqs) != 2:
        return None
    (a1, b1, c1), (a2, b2, c2) = eqs
    sol = _solve_2x2_cramer(a1, b1, c1, a2, b2, c2)
    if sol is None:
        return None
    x, y = sol
    return str(x + y)

def _handle_nCk(text: str) -> Optional[str]:
    t = text.lower()
    m = _NCK_RE_1.search(t)
    if not m:
        m = _NCK_RE_2.search(text)
    if not m:
        return None
    n = int(m.group(1)); k = int(m.group(2))
    if k < 0 or n < 0 or k > n:
        return None
    if n > 200000:
        return None
    return str(math.comb(n, k))

def _crt_pair(a1: int, m1: int, a2: int, m2: int) -> Optional[Tuple[int, int]]:
    g = math.gcd(m1, m2)
    if (a2 - a1) % g != 0:
        return None
    l = (m1 // g) * m2
    m1g = m1 // g
    m2g = m2 // g
    rhs = (a2 - a1) // g
    if m2g == 1:
        return (a1 % l, l)
    inv = _inv_mod(m1g % m2g, m2g)
    if inv is None:
        return None
    t = (rhs % m2g) * inv % m2g
    a = (a1 + m1 * t) % l
    return a, l

def _handle_crt(text: str) -> Optional[str]:
    t = text.lower()
    if "mod" not in t and "≡" not in text:
        return None
    congr = []
    for a_s, m_s in _CONG_RE.findall(text):
        mi0 = int(m_s)
        mi = _safe_mod(mi0)
        if mi is None:
            return None
        if mi == 1:
            continue
        ai = _norm_residue(int(a_s), mi)
        congr.append((ai, mi))
    if len(congr) < 2:
        return None
    a, m = congr[0]
    for ai, mi in congr[1:]:
        res = _crt_pair(a, m, ai, mi)
        if res is None:
            return None
        a, m = res
    return str(a % m)

def _handle_powmod(text: str) -> Optional[str]:
    t = text.lower()
    if "mod" not in t:
        return None
    m = _POWMOD_RE.search(text) or _POWMOD_RE.search(t)
    if not m:
        return None
    a = int(m.group(1)); e = int(m.group(2)); mod0 = int(m.group(3))
    mod = _safe_mod(mod0)
    if mod is None or e < 0:
        return None
    if mod == 1:
        return "0"
    try:
        return str(pow(a, e, mod))
    except Exception:
        return None

def _handle_gcd(text: str) -> Optional[str]:
    m = _GCD_RE.search(text) or _GCD_RE.search(text.lower())
    if not m:
        return None
    return str(math.gcd(int(m.group(1)), int(m.group(2))))

def _handle_lcm(text: str) -> Optional[str]:
    m = _LCM_RE.search(text) or _LCM_RE.search(text.lower())
    if not m:
        return None
    a = int(m.group(1)); b = int(m.group(2))
    if a == 0 or b == 0:
        return "0"
    g = math.gcd(a, b)
    return str(abs(a // g * b))

def _handle_linear_x(text: str) -> Optional[str]:
    t = _norm(text)
    m = re.search(r"([^\r\n=]{1,220}?x[^\r\n=]{0,220}?)\s*=\s*(-?\d+)\b", t, re.IGNORECASE)
    if not m:
        return None
    lhs = m.group(1).replace(" ", "")
    rhs = int(m.group(2))
    if lhs.lower().count("x") != 1:
        return None
    if re.search(r"[^0-9xX+\-*]", lhs):
        return None
    if lhs[0] not in "+-":
        lhs = "+" + lhs
    terms = re.findall(r"[+-][^+-]+", lhs)
    a = 0; k = 0
    for term in terms:
        sign = -1 if term[0] == "-" else 1
        body = term[1:]
        low = body.lower()
        if "x" in low:
            coeff_str = low.replace("x", "").replace("*", "")
            if coeff_str == "":
                coeff = 1
            else:
                if not re.fullmatch(r"\d+", coeff_str):
                    return None
                coeff = int(coeff_str)
            a += sign * coeff
        else:
            if not re.fullmatch(r"\d+", body):
                return None
            k += sign * int(body)
    if a == 0:
        return None
    num = rhs - k
    if num % a != 0:
        return None
    return str(num // a)

def _handle_fact_digitsum(text: str) -> Optional[str]:
    t = text.lower()
    if ("digit sum" not in t) and ("sum of digits" not in t):
        return None
    if "!" not in text and "factorial" not in t:
        return None
    n = None
    m = re.search(r"(\d+)\s*!", text)
    if m:
        n = int(m.group(1))
    else:
        m2 = re.search(r"factorial\s*(?:of)?\s*(\d+)", t)
        if m2:
            n = int(m2.group(1))
    if n is None:
        return None
    CAP = 20000
    if n < 0 or n > CAP:
        return None
    f = math.factorial(n)
    ds = sum(ord(ch) - 48 for ch in str(f))
    return str(ds)

class Solver:
    def solve(self, prompt: str) -> str:
        s = _norm(prompt)
        try:
            for fn in (
                _handle_system_sum,
                _handle_nCk,
                _handle_crt,
                _handle_powmod,
                _handle_gcd,
                _handle_lcm,
                _handle_linear_x,
                _handle_fact_digitsum,
            ):
                out = fn(s)
                if out is not None:
                    out = out.strip()
                    return out if re.fullmatch(r"-?\d+", out) else "0"
        except Exception:
            return "0"
        v = _first_int(s)
        return str(v if v is not None else 0)

if __name__ == "__main__":
    import sys
    ans = Solver().solve(sys.stdin.read()).strip()
    if not re.fullmatch(r"-?\d+", ans):
        ans = "0"
    sys.stdout.write(ans)
