# solver.py
import re
import math
from typing import Optional, Tuple, List

_INT_RE = re.compile(r"-?\d+")
_EQ_RE = re.compile(r"(?P<lhs>[^\r\n=]{1,140}?[xy][^\r\n=]{0,140}?)\s*=\s*(?P<rhs>-?\d+)\b", re.IGNORECASE)
_CONG_RE = re.compile(r"x\s*≡\s*(-?\d+)\s*\(\s*mod\s*(\d+)\s*\)", re.IGNORECASE)

def _norm(s: str) -> str:
    s = s.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
    s = s.replace("\u00d7", "*").replace("\u00b7", "*")
    s = s.replace("−", "-")
    return s

def _first_int(s: str) -> Optional[int]:
    m = _INT_RE.search(s)
    return int(m.group(0)) if m else None

def _math_segment(s: str) -> str:
    # take the last plausible math segment (strip leading prose like "Solve for x:")
    s = _norm(s)
    s = s.replace("\r", " ").replace("\n", " ")
    # keep only segments composed of math-ish tokens
    segs = re.findall(r"[0-9xXyY+\-*\s]{1,220}", s)
    segs = [seg.strip() for seg in segs if seg and ("x" in seg.lower() or "y" in seg.lower()) and re.search(r"\d", seg)]
    return segs[-1] if segs else s

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
        lhs_expr = _math_segment(lhs)
        parsed = _parse_lhs_ax_by_const(lhs_expr)
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
    m = re.search(r"\b(?:c|choose)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", t)
    if not m:
        m = re.search(r"\b(\d+)\s*c\s*(\d+)\b", t)
    if not m:
        if "nck" not in t and "binomial" not in t and "comb" not in t and "c(" not in t:
            return None
        # fallback: "Compute C(n,k)" variants with uppercase C
        m = re.search(r"\bC\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", text)
    if not m:
        return None
    n = int(m.group(1)); k = int(m.group(2))
    if k < 0 or n < 0 or k > n:
        return None
    return str(math.comb(n, k))

def _crt_pair(a1: int, m1: int, a2: int, m2: int) -> Optional[Tuple[int, int]]:
    # returns (a, m) with x ≡ a (mod m)
    g = math.gcd(m1, m2)
    if (a2 - a1) % g != 0:
        return None
    l = m1 // g * m2
    m1g = m1 // g
    m2g = m2 // g
    # solve m1 * t ≡ (a2-a1) (mod m2)
    # reduce: m1g * t ≡ (a2-a1)/g (mod m2g)
    rhs = (a2 - a1) // g
    inv = pow(m1g % m2g, -1, m2g)
    t = (rhs % m2g) * inv % m2g
    a = (a1 + m1 * t) % l
    return a, l

def _handle_crt(text: str) -> Optional[str]:
    t = text.lower()
    if "≡" not in text and "mod" not in t:
        return None
    congr = [(int(a), int(m)) for (a, m) in _CONG_RE.findall(text)]
    if len(congr) < 2:
        return None
    a, m = congr[0][0] % congr[0][1], congr[0][1]
    for (ai, mi) in congr[1:]:
        ai = ai % mi
        res = _crt_pair(a, m, ai, mi)
        if res is None:
            return None
        a, m = res
    return str(a)

def _handle_powmod(text: str) -> Optional[str]:
    t = text.lower()
    if "mod" not in t:
        return None
    m = re.search(r"(-?\d+)\s*\^\s*(-?\d+)\s*mod\s*(-?\d+)", t)
    if not m:
        m = re.search(r"(-?\d+)\s*\*\*\s*(-?\d+)\s*mod\s*(-?\d+)", t)
    if not m:
        return None
    a = int(m.group(1)); e = int(m.group(2)); mod = int(m.group(3))
    if mod == 0 or e < 0:
        return None
    return str(pow(a, e, mod))

def _handle_gcd(text: str) -> Optional[str]:
    t = text.lower()
    if "gcd" not in t:
        return None
    m = re.search(r"gcd\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)", t)
    if not m:
        return None
    a = int(m.group(1)); b = int(m.group(2))
    return str(math.gcd(a, b))

def _handle_lcm(text: str) -> Optional[str]:
    t = text.lower()
    if "lcm" not in t:
        return None
    m = re.search(r"lcm\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)", t)
    if not m:
        return None
    a = int(m.group(1)); b = int(m.group(2))
    if a == 0 or b == 0:
        return "0"
    g = math.gcd(a, b)
    return str(abs(a // g * b))

def _handle_linear_x(text: str) -> Optional[str]:
    t = _norm(text)
    # pick the first equation that ends with "= <int>"
    m = re.search(r"([^\r\n=]{1,220}?x[^\r\n=]{0,220}?)\s*=\s*(-?\d+)\b", t, re.IGNORECASE)
    if not m:
        return None
    lhs_raw = m.group(1)
    rhs = int(m.group(2))
    lhs_expr = _math_segment(lhs_raw)
    if lhs_expr.lower().count("x") != 1:
        return None
    lhs_expr = lhs_expr.replace(" ", "")
    if re.search(r"[^0-9xX+\-*]", lhs_expr):
        return None
    if lhs_expr[0] not in "+-":
        lhs_expr = "+" + lhs_expr
    terms = re.findall(r"[+-][^+-]+", lhs_expr)
    a = 0
    k = 0
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

        out = _handle_system_sum(s)
        if out is not None:
            return out

        out = _handle_nCk(s)
        if out is not None:
            return out

        out = _handle_crt(s)
        if out is not None:
            return out

        out = _handle_powmod(s)
        if out is not None:
            return out

        out = _handle_gcd(s)
        if out is not None:
            return out

        out = _handle_lcm(s)
        if out is not None:
            return out

        out = _handle_linear_x(s)
        if out is not None:
            return out

        out = _handle_fact_digitsum(s)
        if out is not None:
            return out

        v = _first_int(s)
        return str(v if v is not None else 0)

if __name__ == "__main__":
    import sys
    data = sys.stdin.read()
    ans = Solver().solve(data).strip()
    if not re.fullmatch(r"-?\d+", ans):
        ans = "0"
    sys.stdout.write(ans)
