from evaluation.combinatorics.sequence_discovery import berlekamp_massey, solve_recurrence

def try_sequence_extrapolation(values, target_n):
    coeffs = berlekamp_massey(values)
    if not coeffs:
        return None
    return solve_recurrence(coeffs, values, target_n)
