# evaluation/discrete_solver.py
# Deterministic number theory + combinatorics engine (stdlib only)

from math import isqrt
from functools import lru_cache

# ---------- Number Theory ----------

def egcd(a, b):
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = egcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)

def modinv(a, m):
    g, x, _ = egcd(a, m)
    if g != 1:
        raise ValueError("No modular inverse")
    return x % m

def crt(pairs):
    # pairs = [(a1, m1), (a2, m2), ...]
    x, m = pairs[0]
    for a2, m2 in pairs[1:]:
        g, s, t = egcd(m, m2)
        if (a2 - x) % g != 0:
            raise ValueError("No CRT solution")
        lcm = m * m2 // g
        x = (x + (a2 - x) // g * s % (m2 // g) * m) % lcm
        m = lcm
    return x, m

def sieve(n):
    is_prime = [True] * (n + 1)
    is_prime[0:2] = [False, False]
    for i in range(2, isqrt(n) + 1):
        if is_prime[i]:
            for j in range(i*i, n+1, i):
                is_prime[j] = False
    return [i for i, v in enumerate(is_prime) if v]

# ---------- Combinatorics ----------

@lru_cache(None)
def binom(n, k):
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    return binom(n-1, k-1) + binom(n-1, k)

def count_subsets(n):
    # 2^n deterministically
    return 1 << n
