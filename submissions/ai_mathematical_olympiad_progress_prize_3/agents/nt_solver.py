import re
from fractions import Fraction

class NTSolver:
    def _normalize(self, text):
        if not text or not isinstance(text, str):
            return ""
        text = re.sub(r'\\\(|\\\)|\\\[|\\\]|\$', '', text)
        text = re.sub(r'Solve|for x\.?|What is', '', text, flags=re.IGNORECASE)
        text = text.replace('\\times', '*').replace('\\cdot', '*').replace('\u2212', '-')
        text = text.replace(' ', '').rstrip('.?!')
        text = re.sub(r'x\*?([0-9/\.]+)', r'\1x', text, flags=re.IGNORECASE)
        text = re.sub(r'([0-9/\.]+)\*x', r'\1x', text, flags=re.IGNORECASE)
        text = text.replace('*x', 'x').replace('*X', 'x').replace('X', 'x')
        def eval_mul(m):
            try:
                return str(Fraction(m.group(1)) * Fraction(m.group(2)))
            except:
                return m.group(0)
        text = re.sub(r'([0-9/\.]+)\*([0-9/\.]+)', eval_mul, text)
        return text

    def _reduce_to_ab(self, expr):
        expr = expr.replace('--', '+').replace('+-', '-').replace('-+', '-')
        if not expr.startswith('+') and not expr.startswith('-'):
            expr = '+' + expr
        pattern = r'([+-])([0-9/\.]*)(x?)'
        matches = re.findall(pattern, expr, re.IGNORECASE)
        a, b = Fraction(0), Fraction(0)
        for sign, val_str, has_x in matches:
            if not val_str and not has_x:
                continue
            try:
                val = Fraction(val_str) if val_str else Fraction(1)
            except:
                continue
            if sign == '-':
                val = -val
            if has_x:
                a += val
            else:
                b += val
        return a, b

    def solve(self, problem):
        if not isinstance(problem, str) or problem.endswith('.csv'):
            return 0
        clean = self._normalize(problem)
        if '=' not in clean:
            _, res = self._reduce_to_ab(clean)
        else:
            parts = clean.split('=')
            if len(parts) != 2:
                return 0
            a1, b1 = self._reduce_to_ab(parts[0])
            a2, b2 = self._reduce_to_ab(parts[1])
            A, B = a1 - a2, b2 - b1
            if A == 0:
                return 0
            res = B / A
        return int(res) if res.denominator == 1 else f"{res.numerator}/{res.denominator}"
