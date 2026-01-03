"""
BERLEKAMP-MASSEY OPTIMIZER (DSS-Ω APEX MODULE)
----------------------------------------------
Deterministic, exact (Fraction-based) linear recurrence synthesis.
"""

from fractions import Fraction

def find_linear_recurrence(sequence):
    N = len(sequence)
    C = [Fraction(1)]
    B = [Fraction(1)]
    L = 0
    m = 1
    b = Fraction(1)

    for n in range(N):
        d = sequence[n]
        for i in range(1, L + 1):
            d += C[i] * sequence[n - i]

        if d == 0:
            m += 1
        else:
            T = list(C)
            factor = d / b
            shift_B = [Fraction(0)] * m + B
            if len(C) < len(shift_B):
                C += [Fraction(0)] * (len(shift_B) - len(C))
            for i in range(len(shift_B)):
                C[i] -= factor * shift_B[i]

            if 2 * L <= n:
                L = n + 1 - L
                B = T
                b = d
                m = 1
            else:
                m += 1

    return [-c for c in C[1:]]

def predict_next_term(sequence, coeffs):
    L = len(coeffs)
    if len(sequence) < L:
        return None
    next_val = Fraction(0)
    for i in range(L):
        next_val += coeffs[i] * sequence[-1 - i]
    return next_val
