import re
from fractions import Fraction
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

def nCr(n, r):
    if r < 0 or r > n:
        return 0
    r = min(r, n - r)
    num = den = 1
    for i in range(1, r + 1):
        num *= n - r + i
        den *= i
    return num // den

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

class Solver:
    def solve(self, problem):
        p = problem.lower()

        # geometry: distance squared
        if "distance" in p:
            nums = list(map(int, re.findall(r"-?\d+", p)))
            if len(nums) == 4:
                x1, y1, x2, y2 = nums
                return (x1 - x2)**2 + (y1 - y2)**2

        # linear equation ax+b=0
        m = re.match(r"([+-]?\d*)x([+-]\d+)=0", p.replace(" ", ""))
        if m:
            a = int(m.group(1) or 1)
            b = int(m.group(2))
            return Fraction(-b, a)

        # CRT
        matches = re.findall(r"x\s*=\s*(\d+)\s*\(mod\s*(\d+)\)", p)
        if matches:
            congruences = [(int(r), int(m)) for r, m in matches]
            res = crt(congruences)
            if res is not None:
                return res

        # prime factorization
        if "prime factor" in p:
            nums = re.findall(r"\d+", p)
            if nums:
                pf = prime_factors(int(nums[0]))
                return "*".join(f"{k}^{v}" for k, v in sorted(pf.items()))

        # combinatorics
        if "choose" in p or "how many ways" in p:
            nums = list(map(int, re.findall(r"\d+", p)))
            if len(nums) >= 2:
                return nCr(max(nums), min(nums))

        return 0

def solve(problem):
    return Solver().solve(problem)
