from .solver_base import SolverBase
import sympy as sp
import re

class GeoSolver(SolverBase):
    domain = "GEO"

    def solve(self, problem_text):
        t = problem_text.lower()
        if "distance" in t:
            nums = list(map(int, re.findall(r'-?\d+', t)))
            if len(nums) == 4:
                x1,y1,x2,y2 = nums
                return sp.sqrt((x2-x1)**2 + (y2-y1)**2)
        return None
