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
# === AIMO-3 EXPANSION: GEOMETRY DISPATCH (EXACT) ===

def _extract_distance(problem):
    if 'distance' in problem.lower():
        nums = re.findall(r'-?\d+', problem)
        if len(nums) == 4:
            return tuple(map(int, nums))
    return None

class Solver(Solver):
    def solve(self, problem):
        # geometry: distance squared
        dist_args = _extract_distance(problem)
        if dist_args:
            x1, y1, x2, y2 = dist_args
            return (x1 - x2)**2 + (y1 - y2)**2

        return super().solve(problem)

import re
from fractions import Fraction

def _solve_linear(a, b):
    # ax + b = 0
    if a == 0:
        return None
    return Fraction(-b, a)

    # ax^2 + bx + c = 0 (exact, discriminant check)
    if a == 0:
        return _solve_linear(b, c)
    d = b*b - 4*a*c
    if d < 0:
        return None
    s = int(d**0.5)
    if s*s != d:
        return None
    r1 = Fraction(-b + s, 2*a)
    r2 = Fraction(-b - s, 2*a)
    return r1 if r1 == r2 else str(r1) + "," + str(r2)

class Solver(Solver):
    def solve(self, problem):
        p = problem.replace(' ', '').lower()

        # linear ax+b=0
        m = re.match(r'([+-]?\d*)x([+-]\d+)=0', p)
        if m:
            a = int(m.group(1) or 1)
            b = int(m.group(2))
            res = _solve_linear(a, b)
            if res is not None:
                return res

        m = re.match(r'([+-]?\d*)x\^2([+-]\d*)x([+-]\d+)=0', p)
        if m:
            a = int(m.group(1) or 1)
            b = int(m.group(2) or 1)
            c = int(m.group(3))
            if res is not None:
                return res

        return super().solve(problem)

# === AIMO-3 FIX: COMBINATORICS + GEOMETRY DISPATCH ===

def _extract_nCr(problem):
    p = problem.lower()
    if 'choose' in p or 'how many ways' in p:
        nums = list(map(int, re.findall(r'\d+', p)))
        if len(nums) >= 2:
            return max(nums), min(nums)
    return None

def _extract_distance(problem):
    p = problem.lower()
    if 'distance' in p:
        nums = list(map(int, re.findall(r'-?\d+', p)))
        if len(nums) == 4:
            return nums
    return None

class Solver(Solver):
    def solve(self, problem):
        # combinatorics
        comb = _extract_nCr(problem)
        if comb:
            n, r = comb
            return nCr(n, r)

        # geometry: distance squared
        dist = _extract_distance(problem)
        if dist:
            x1, y1, x2, y2 = dist
            return (x1 - x2)**2 + (y1 - y2)**2

        return super().solve(problem)
