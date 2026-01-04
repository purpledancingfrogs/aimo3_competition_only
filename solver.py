import re
import math
from fractions import Fraction
from collections import defaultdict

# =========================
# Exact Number Theory Core
# =========================

def egcd(a, b):
    if b == 0:
        return a, 1, 0
    g, x1, y1 = egcd(b, a % b)
    return g, y1, x1 - (a // b) * y1

def mod_inverse(a, m):
    g, x, _ = egcd(a, m)
    if g != 1:
        return None
    return x % m

def crt(congruences):
    x, m = 0, 1
    for r, mod in congruences:
        inv = mod_inverse(m, mod)
        if inv is None:
            return None
        x = (r - x) * inv % mod * m + x
        m *= mod
        x %= m
    return x

def prime_factors(n):
    factors = defaultdict(int)
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] += 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        factors[n] += 1
    return dict(factors)

# =========================
# Exact Combinatorics
# =========================

def nCr(n, r):
    if r < 0 or r > n:
        return 0
    r = min(r, n - r)
    num = 1
    den = 1
    for i in range(1, r + 1):
        num *= n - r + i
        den *= i
    return num // den

# =========================
# Geometry (Exact Analytic)
# =========================

def dist_sq(x1, y1, x2, y2):
    return (x1 - x2)**2 + (y1 - y2)**2

# =========================
# Solver
# =========================

class Solver:
    def solve(self, problem):
        p = problem.lower()

        # --- Combinatorics ---
        if any(k in p for k in ["how many ways", "choose", "combination"]):
            nums = list(map(int, re.findall(r"\d+", p)))
            if len(nums) >= 2:
                return nCr(max(nums), min(nums))

        # --- Modular / CRT ---
        if "mod" in p or "remainder" in p or "=" in p:
            mods = re.findall(r"x\s*=\s*(\d+)\s*\(mod\s*(\d+)\)", p)
            if mods:
                congruences = [(int(r), int(m)) for r, m in mods]
                res = crt(congruences)
                if res is not None:
                    return res

        # --- Prime factorization ---
        if "prime factor" in p:
            nums = list(map(int, re.findall(r"\d+", p)))
            if nums:
                pf = prime_factors(nums[0])
                out = []
                for k in sorted(pf):
                    out.append(f"{k}^{pf[k]}")
                return "*".join(out)

        # --- Geometry distance ---
        if "distance" in p:
            nums = list(map(int, re.findall(r"-?\d+", p)))
            if len(nums) == 4:
                return dist_sq(nums[0], nums[1], nums[2], nums[3])

        return 0

def solve(problem):
    return Solver().solve(problem)
# === AIMO-3 EXPANSION: NUMBER THEORY CORE ===
from collections import defaultdict

def prime_factors(n):
    f = defaultdict(int)
    d = 2
    while d * d <= n:
        while n % d == 0:
            f[d] += 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        f[n] += 1
    return dict(f)
# === AIMO-3 EXPANSION: CHINESE REMAINDER THEOREM ===

def egcd(a, b):
    if b == 0:
        return a, 1, 0
    g, x1, y1 = egcd(b, a % b)
    return g, y1, x1 - (a // b) * y1

def mod_inverse(a, m):
    g, x, _ = egcd(a, m)
    if g != 1:
        return None
    return x % m

def crt(congruences):
    x, m = 0, 1
    for r, mod in congruences:
        inv = mod_inverse(m, mod)
        if inv is None:
            return None
        x = (r - x) * inv % mod * m + x
        m *= mod
        x %= m
    return x
# === AIMO-3 DISPATCH INTEGRATION: NUMBER THEORY ===

import re

def _extract_crt(problem):
    matches = re.findall(r'x\s*=\s*(-?\d+)\s*\(mod\s*(\d+)\)', problem)
    if matches:
        return [(int(r), int(m)) for r, m in matches]
    return None

def _extract_prime_factor_target(problem):
    if 'prime factor' in problem.lower():
        nums = re.findall(r'\d+', problem)
        if nums:
            return int(nums[0])
    return None

class Solver:
    def solve(self, problem):
        p = problem.lower()

        # --- CRT ---
        congruences = _extract_crt(p)
        if congruences:
            res = crt(congruences)
            if res is not None:
                return res

        # --- Prime Factorization ---
        n = _extract_prime_factor_target(p)
        if n is not None:
            pf = prime_factors(n)
            return "*".join(f"{k}^{v}" for k, v in sorted(pf.items()))

        return 0
