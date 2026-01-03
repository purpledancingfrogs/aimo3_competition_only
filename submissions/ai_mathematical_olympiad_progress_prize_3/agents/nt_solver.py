import re
from fractions import Fraction

class SymbolicTerm:
    def __init__(self, a=0, b=0):
        self.a = Fraction(a)
        self.b = Fraction(b)
    def __add__(self, o): return SymbolicTerm(self.a + o.a, self.b + o.b)
    def __sub__(self, o): return SymbolicTerm(self.a - o.a, self.b - o.b)
    def __mul__(self, o):
        if self.a != 0 and o.a != 0: return SymbolicTerm(0, 0)
        return SymbolicTerm(self.a * o.b + o.a * self.b, self.b * o.b)
    def __truediv__(self, o):
        if o.a != 0 or o.b == 0: return SymbolicTerm(0, 0)
        return SymbolicTerm(self.a / o.b, self.b / o.b)

class NTSolver:
    def _normalize(self, text):
        if not text or not isinstance(text, str): return ""
        text = re.sub(r'\\\(|\\\)|\\\[|\\\]|\$', '', text)
        text = re.sub(r'(?i)Solve|for x\.?|What is', '', text)
        text = text.replace('\\times', '*').replace('\\cdot', '*').replace('\u2212', '-')
        text = text.replace(' ', '').rstrip('.?!').replace('^', '**')
        text = re.sub(r'(\d)(x)', r'\1*\2', text, flags=re.I)
        return text

    def _evaluate(self, expr):
        tokens = re.findall(r'\d+\.\d+|\d+|x|[\+\-\*\/\(\)]', expr.lower())
        ops, values = [], []
        prec = {'+':1,'-':1,'*':2,'/':2}
        def apply():
            if not ops or len(values) < 2: return
            op = ops.pop()
            r = values.pop()
            l = values.pop()
            if op == '+': values.append(l + r)
            elif op == '-': values.append(l - r)
            elif op == '*': values.append(l * r)
            elif op == '/': values.append(l / r)
        for i,t in enumerate(tokens):
            if t == '(':
                ops.append(t)
            elif t == ')':
                while ops and ops[-1] != '(':
                    apply()
                if ops: ops.pop()
            elif t in '+-*/':
                if t == '-' and (i == 0 or tokens[i-1] in '(+-*/'):
                    values.append(SymbolicTerm(0,0))
                while ops and ops[-1] != '(' and prec.get(ops[-1],0) >= prec[t]:
                    apply()
                ops.append(t)
            elif t == 'x':
                values.append(SymbolicTerm(1,0))
            else:
                values.append(SymbolicTerm(0,t))
        while ops:
            apply()
        return values[0] if values else SymbolicTerm(0,0)

    def solve(self, problem):
        if not isinstance(problem,str) or problem.endswith('.csv') or not problem:
            return 0
        clean = self._normalize(problem)
        try:
            if '=' in clean:
                l,r = clean.split('=')
                L,R = self._evaluate(l), self._evaluate(r)
                A = L.a - R.a
                B = R.b - L.b
                if A == 0: return 0
                res = B / A
            else:
                res = self._evaluate(clean).b
            return int(res) if res.denominator == 1 else f"{res.numerator}/{res.denominator}"
        except:
            return 0
