from .solver_base import SolverBase
import re
from sympy import factorint, isprime

class NTSolver(SolverBase):
    domain = "NT"

    def solve(self, problem_text):
        t = problem_text.lower()

        # basic arithmetic
        m = re.search(r'(-?\d+)\s*[-+*/]\s*(-?\d+)', t)
        if m:
            try:
                return eval(m.group(0))
            except:
                pass

        # multiplication phrasing
        nums = re.findall(r'-?\d+', t)
        if "times" in t and len(nums) == 2:
            return int(nums[0]) * int(nums[1])

        # primality
        if "prime" in t and nums:
            return int(isprime(int(nums[0])))

        # factorization count
        if "factor" in t and nums:
            return factorint(int(nums[0]))

        return None
