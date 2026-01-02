from fractions import Fraction

def berlekamp_massey(sequence):
    # Deterministic BM over rationals
    s = [Fraction(x) for x in sequence]
    C = [Fraction(1)]
    B = [Fraction(1)]
    L, m, b = 0, 1, Fraction(1)

    for n in range(len(s)):
        d = sum(C[i] * s[n - i] for i in range(1, L + 1)) + s[n]
        if d == 0:
            m += 1
        else:
            T = C[:]
            coef = d / b
            while len(C) < len(B) + m:
                C.append(Fraction(0))
            for i in range(len(B)):
                C[i + m] -= coef * B[i]
            if 2 * L > n:
                m += 1
            else:
                B = T
                b = d
                L = n + 1 - L
                m = 1
    return C[1:]

def solve_recurrence(coeffs, init, n):
    # Linear recurrence evaluation via DP (deterministic)
    k = len(coeffs)
    dp = list(init)
    for i in range(len(init), n + 1):
        val = sum(coeffs[j] * dp[i - j - 1] for j in range(k))
        dp.append(val)
    return dp[n]
