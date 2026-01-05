from __future__ import annotations

def pow_mod(a: int, b: int, m: int) -> int:
    if m == 0:
        raise ValueError("mod 0")
    return pow(int(a) % m, int(b), int(m))

def egcd(a: int, b: int):
    a = int(a); b = int(b)
    x0, x1, y0, y1 = 1, 0, 0, 1
    while b:
        q = a // b
        a, b = b, a - q*b
        x0, x1 = x1, x0 - q*x1
        y0, y1 = y1, y0 - q*y1
    return a, x0, y0

def inv_mod(a: int, m: int) -> int:
    g, x, _ = egcd(a, m)
    if g != 1 and g != -1:
        raise ValueError("no inverse")
    return x % m

def crt_small(congruences):
    """
    congruences: iterable of (r_i, m_i) with pairwise coprime m_i
    returns (r, M) such that r ≡ r_i (mod m_i), M = prod m_i
    """
    r = 0
    M = 1
    for (ri, mi) in congruences:
        ri = int(ri); mi = int(mi)
        if mi <= 0:
            raise ValueError("bad modulus")
        if M == 1:
            r = ri % mi
            M = mi
            continue
        # combine r + M*t ≡ ri (mod mi)
        t = ((ri - r) % mi) * inv_mod(M % mi, mi) % mi
        r = r + M * t
        M = M * mi
        r %= M
    return r, M

def v_p_factorial(n: int, p: int) -> int:
    n = int(n); p = int(p)
    if n < 0 or p <= 1:
        raise ValueError("bad args")
    s = 0
    while n:
        n //= p
        s += n
    return s

def v_p_binom_legendre(n: int, k: int, p: int) -> int:
    n = int(n); k = int(k); p = int(p)
    if k < 0 or k > n:
        return 0
    return v_p_factorial(n, p) - v_p_factorial(k, p) - v_p_factorial(n-k, p)

def carries_in_base_p(n: int, k: int, p: int) -> int:
    # Kummer: v_p(C(n,k)) equals number of carries when adding k and n-k in base p
    n = int(n); k = int(k); p = int(p)
    if k < 0 or k > n:
        return 0
    a = k
    b = n - k
    carries = 0
    carry = 0
    while a > 0 or b > 0 or carry:
        da = a % p
        db = b % p
        a //= p
        b //= p
        if da + db + carry >= p:
            carries += 1
            carry = 1
        else:
            carry = 0
    return carries
