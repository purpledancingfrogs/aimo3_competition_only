import re, math, unicodedata
_GHOSTS = ['\u200b', '\u200c', '\u200d', '\u2060', '\ufeff', '\u202a', '\u202c']
def normalize_math_text(s):
    s = unicodedata.normalize('NFKC', str(s))
    for um in ['\u2212', '\u2013', '\u2014', '\u2015', '\u2010', '\u2011']: s = s.replace(um, '-')
    for zw in _GHOSTS: s = s.replace(zw, '')
    return re.sub(r'\+\s*-', '- ', ' '.join(s.split())).strip()
_FC = {}
def factorial_digit_sum(n):
    if n not in _FC: _FC[n] = math.factorial(n)
    return sum(int(d) for d in str(_FC[n]))
_FDS_RE = re.compile(r'sum\s+of\s+(?:the\s+)?digits.*?(\d+)\s*!', re.I)
def try_factorial_digit_sum(t):
    m = _FDS_RE.search(t)
    return factorial_digit_sum(int(m.group(1))) if m and 0 <= int(m.group(1)) <= 500 else None
_LIN_RE = re.compile(r'solve.*?x.*?(-?\d+)\s*\*?\s*x\s*([+\-])\s*(-?\d+)\s*=\s*(-?\d+)', re.I)
def try_linear_equation(t):
    m = _LIN_RE.search(normalize_math_text(t))
    if m:
        a, sign, b, c = int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4))
        if sign == '-': b = -b
        if a != 0 and (c - b) % a == 0: return abs((c - b) // a)
    return None
_SYS_RE = re.compile(r'(-?\d+)\s*\*?\s*x\s*([+\-])\s*(\d+)\s*\*?\s*y\s*=\s*(-?\d+)\s+(-?\d+)\s*\*?\s*x\s*([+\-])\s*(\d+)\s*\*?\s*y\s*=\s*(-?\d+)', re.I)
def try_2x2_system(t):
    if not re.search(r'return\s+x\s*\+\s*y|find\s+x\s*\+\s*y', t, re.I): return None
    m = _SYS_RE.search(normalize_math_text(t))
    if m:
        a1, b1, c1 = int(m.group(1)), int(m.group(3))*(1 if m.group(2)=='+' else -1), int(m.group(4))
        a2, b2, c2 = int(m.group(5)), int(m.group(7))*(1 if m.group(6)=='+' else -1), int(m.group(8))
        det = a1*b2 - a2*b1
        if det != 0:
            dx, dy = c1*b2 - c2*b1, a1*c2 - a2*c1
            if dx % det == 0 and dy % det == 0: return abs(dx//det + dy//det)
    return None
def egcd(a, b): return (a, 1, 0) if b == 0 else (lambda g,x,y: (g, y, x-(a//b)*y))(*egcd(b, a%b))
def crt2(a1, m1, a2, m2):
    g, p, _ = egcd(m1, m2)
    if (a2 - a1) % g != 0: return None
    return (a1 + m1 * ((a2 - a1) // g) * p) % (m1 // g * m2)
_CRT_RE = re.compile(r'x\s*[=\u2261]\s*(-?\d+)\s*\(?mod\s*(\d+)\)?.*?x\s*[=\u2261]\s*(-?\d+)\s*\(?mod\s*(\d+)\)?', re.I)
def try_crt(t):
    m = _CRT_RE.search(normalize_math_text(t))
    return crt2(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))) if m else None
_GCD_RE = re.compile(r'gcd\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', re.I)
_LCM_RE = re.compile(r'lcm\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', re.I)
def try_gcd(t):
    m = _GCD_RE.search(t)
    return math.gcd(int(m.group(1)), int(m.group(2))) if m else None
def try_lcm(t):
    m = _LCM_RE.search(t)
    return (int(m.group(1)) * int(m.group(2))) // math.gcd(int(m.group(1)), int(m.group(2))) if m else None
def apex_dispatch(p):
    for fn in [try_factorial_digit_sum, try_gcd, try_lcm, try_crt, try_2x2_system, try_linear_equation]:
        r = fn(p)
        if r is not None: return r
    return None
def solve(problem):
    s = str(problem).strip()
    m = re.fullmatch(r'\s*(\d+)\s*([+\-*])\s*(\d+)\s*', s)
    if m:
        a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
        v = a+b if op=='+' else (a-b if op=='-' else a*b)
        return str(max(0, min(99999, v)))
    r = apex_dispatch(s)
    if r is not None: return str(abs(int(r)) % 100000)
    return '0'
def predict(problems): return [solve(p) for p in problems]