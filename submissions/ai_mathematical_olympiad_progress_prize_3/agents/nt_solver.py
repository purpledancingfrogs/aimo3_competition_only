import re
from fractions import Fraction

class NTSolver:
    def __init__(self):
        pass

    def _normalize(self, text):
        if not text:
            return ""
        text = re.sub(r'\\\(|\\\)|\\\[|\\\]|\$', '', text)
        text = re.sub(r'Solve|for x\.?|What is', '', text, flags=re.IGNORECASE)
        text = text.replace('\\times', '*').replace('\\cdot', '*').replace('\u2212', '-')
        text = text.replace(' ', '').replace('-', '+-').replace('*x', 'x')
        if text.startswith('+-'):
            text = text[1:]
        return text

    def _reduce_to_ab(self, expr):
        a, b = Fraction(0), Fraction(0)
        terms = [t for t in expr.split('+') if t]
        for term in terms:
            if 'x' in term.lower():
                c = term.lower().replace('x', '')
                if c == '' or c == '+':
                    a += 1
                elif c == '-':
                    a -= 1
                else:
                    try:
                        a += Fraction(c)
                    except Exception:
                        pass
            else:
                try:
                    b += Fraction(term)
                except Exception:
                    pass
        return a, b

    def solve(self, problem):
        if isinstance(problem, str) and (problem.endswith('.csv') or problem.endswith('.parquet')):
            return 0
        clean = self._normalize(problem)
        if '=' not in clean:
            _, val = self._reduce_to_ab(clean)
            return int(val) if val.denominator == 1 else f"{val.numerator}/{val.denominator}"
        parts = clean.split('=')
        if len(parts) != 2:
            return 0
        a1, b1 = self._reduce_to_ab(parts[0])
        a2, b2 = self._reduce_to_ab(parts[1])
        A = a1 - a2
        B = b2 - b1
        if A == 0:
            return 0
        ans = B / A
        return int(ans) if ans.denominator == 1 else f"{ans.numerator}/{ans.denominator}"
