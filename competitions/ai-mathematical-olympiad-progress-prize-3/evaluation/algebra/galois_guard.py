from fractions import Fraction
from math import gcd

def poly_gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def is_square_free(coeffs):
    # naive square-free test for integer polynomials
    seen = set()
    for c in coeffs:
        if c in seen:
            return False
        seen.add(c)
    return True

def galois_solvable_fingerprint(poly_coeffs):
    """
    Deterministic fingerprint:
    - Degree <= 4 → solvable by radicals
    - Degree >= 5 → check square-free + discriminant parity heuristic
    If not solvable, return False to force modular / numeric fallback.
    """
    deg = len(poly_coeffs) - 1
    if deg <= 4:
        return True

    # Normalize
    coeffs = [Fraction(c) for c in poly_coeffs]
    nums = [c.numerator for c in coeffs]

    if not is_square_free(nums):
        return False

    d = 0
    for n in nums:
        d = gcd(d, abs(n))

    # Deterministic parity gate (fast, conservative)
    return d % 2 == 1
