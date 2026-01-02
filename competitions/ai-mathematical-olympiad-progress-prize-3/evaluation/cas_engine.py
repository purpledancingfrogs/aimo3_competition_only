from evaluation.algebra.galois_guard import galois_solvable_fingerprint

def guard_radical_attempt(poly_coeffs):
    if not galois_solvable_fingerprint(poly_coeffs):
        raise RuntimeError("UNSOLVABLE_GALOIS_GROUP")
