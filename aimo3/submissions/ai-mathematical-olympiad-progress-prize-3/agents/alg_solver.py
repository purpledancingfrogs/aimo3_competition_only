from .solver_base import SolverBase
import sympy as sp
import re

class AlgSolver(SolverBase):
    domain = "ALG"

    def solve(self, problem_text):
        txt = problem_text.replace(' ', '')
        x = sp.symbols('x')

        # linear equation ax+b=c
        m = re.search(r'([+-]?\d*)x([+-]\d+)?=([+-]?\d+)', txt)
        if m:
            a = int(m.group(1)) if m.group(1) not in ['', '+', '-'] else (1 if m.group(1) in ['', '+'] else -1)
            b = int(m.group(2)) if m.group(2) else 0
            c = int(m.group(3))
            return sp.solve(a*x + b - c, x)[0]

        return None
