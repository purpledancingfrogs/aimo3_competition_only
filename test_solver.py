from solver_core import dss_omega_solver

tests = [
    ("Compute the sum of 1, 2, 3, and 4.", 10),
    ("Find the gcd of 12 and 18.", 6),
    ("What is 7 + 9?", 16),
    ("Find the product of 3 and 5.", 15),
    ("Compute 2^10.", 1024),
    ("Compute 100 mod 7.", 2),
]

for q, a in tests:
    p = dss_omega_solver(q)
    print(q, "=>", p, "(ok)" if p == a else f"(FAIL expected {a})")
