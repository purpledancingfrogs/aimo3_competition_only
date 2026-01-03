from solver_core import dss_omega_solver

tests = [
    "Compute the sum of 1, 2, 3, and 4.",
    "Find the gcd of 12 and 18.",
    "What is 7 + 9?",
    "Find the product of 3 and 5."
]

for t in tests:
    print(t, "=>", dss_omega_solver(t))
