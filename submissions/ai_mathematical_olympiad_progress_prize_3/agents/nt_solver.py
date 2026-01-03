import re
from sympy import symbols, Eq, solve
from sympy.parsing.sympy_parser import parse_expr

class NTSolver:
    def solve(self, problem_text):
        if not problem_text:
            return None

        t = problem_text.lower()

        # normalize latex / symbols
        t = t.replace('\\\\times', '*').replace('×', '*').replace('$', '')
        t = t.replace('?', '').strip()

        # subtraction
        m = re.search(r'(-?\d+)\s*-\s*(-?\d+)', t)
        if m:
            return int(m.group(1)) - int(m.group(2))

        # multiplication
        m = re.search(r'(-?\d+)\s*\*\s*(-?\d+)', t)
        if m:
            return int(m.group(1)) * int(m.group(2))

        # linear equation solve ax=b or ax=c
        if 'solve' in t and 'x' in t and '=' in t:
            try:
                x = symbols('x')
                expr = re.sub(r'[^0-9x=+\-*/]', '', t)
                lhs, rhs = expr.split('=')
                sol = solve(Eq(parse_expr(lhs), parse_expr(rhs)), x)
                if sol:
                    return int(sol[0])
            except:
                return None

        return None
