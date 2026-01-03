import re
from fractions import Fraction

def solve(problem: str):
    if not isinstance(problem, str) or not problem:
        return 0

    s = problem.lower()
    s = re.sub(r'\\\(|\\\)|\\\[|\\\]|\$', '', s)
    s = re.sub(r'what is|solve|for x\.?', '', s)
    s = s.replace(' ', '').replace('−', '-').replace('×', '*').replace('^', '**')
    s = re.sub(r'(\d)(x)', r'\1*x', s)

    def eval_simple(expr):
        try:
            return Fraction(eval(expr, {"__builtins__": {}}, {}))
        except:
            return Fraction(0)

    if '=' not in s:
        v = eval_simple(s)
        return int(v) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"

    l, r = s.split('=', 1)
    try:
        # ax+b = cx+d  →  (a-c)x = d-b
        def coeff(expr):
            expr = expr.replace('-', '+-')
            a = Fraction(0)
            b = Fraction(0)
            for t in expr.split('+'):
                if not t:
                    continue
                if 'x' in t:
                    c = t.replace('*x', '').replace('x', '')
                    a += Fraction(c) if c not in ('', '+', '-') else Fraction(1 if c != '-' else -1)
                else:
                    b += Fraction(t)
            return a, b

        a1, b1 = coeff(l)
        a2, b2 = coeff(r)
        A = a1 - a2
        B = b2 - b1
        if A == 0:
            return 0
        res = B / A
        return int(res) if res.denominator == 1 else f"{res.numerator}/{res.denominator}"
    except:
        return 0
