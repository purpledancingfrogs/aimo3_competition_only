# evaluation/discrete_solver.py
# Deterministic Number Theory + Combinatorics Engine (Standard Library Only)

from functools import lru_cache
from math import gcd

# ---------------- Number Theory ----------------

def egcd(a, b):
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = egcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)

def modinv(a, m):
    g, x, _ = egcd(a, m)
    if g != 1:
        return None
    return x % m

def crt(congruences):
    # congruences = [(a1, m1), (a2, m2), ...]
    x, M = 0, 1
    for a, m in congruences:
        inv = modinv(M, m)
        if inv is None:
            return None
        x = (a - x) * inv % m * M + x
        M *= m
        x %= M
    return x, M

def smallest_solution(predicate, limit=1_000_000):
    for n in range(limit):
        if predicate(n):
            return n
    return None

# ---------------- Combinatorics / DP ----------------

@lru_cache(None)
def binomial(n, k):
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    return binomial(n-1, k-1) + binomial(n-1, k)

@lru_cache(None)
def partitions(n, max_part=None):
    if n == 0:
        return 1
    if n < 0:
        return 0
    if max_part is None or max_part > n:
        max_part = n
    if max_part == 0:
        return 0
    return partitions(n, max_part-1) + partitions(n-max_part, max_part)
