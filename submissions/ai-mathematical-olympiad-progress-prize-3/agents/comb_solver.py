from .solver_base import SolverBase
import math
import re

class CombSolver(SolverBase):
    domain = "COMB"

    def solve(self, problem_text):
        t = problem_text.lower()
        nums = list(map(int, re.findall(r'\d+', t)))

        if 'choose' in t or 'combination' in t:
            n,k = nums
            return math.comb(n,k)

        if 'permutation' in t:
            n,k = nums
            return math.perm(n,k)

        return None
