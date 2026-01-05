from solver_modules.nt_mod import pow_mod, crt_small, v_p_factorial, v_p_binom_legendre, carries_in_base_p

def test_pow_mod():
    assert pow_mod(2, 10, 1000) == 24

def test_crt_small():
    r, M = crt_small([(2,3),(3,5),(2,7)])
    assert M == 105
    assert r % 3 == 2 and r % 5 == 3 and r % 7 == 2

def test_v_p_factorial():
    assert v_p_factorial(10,2) == 8
    assert v_p_factorial(10,5) == 2

def test_v_p_binom_legendre():
    assert v_p_binom_legendre(10,3,2) == carries_in_base_p(10,3,2)
