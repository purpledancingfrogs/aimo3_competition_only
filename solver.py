import re
import math
from fractions import Fraction
from collections import defaultdict

class Polynomial:
    def __init__(self, terms=None):
        self.terms = defaultdict(Fraction)
        if terms:
            for d, v in terms.items():
                if v != 0: self.terms[d] = Fraction(v)
    def __add__(self, o):
        res = defaultdict(Fraction, self.terms)
        for d, v in o.terms.items(): res[d] += v
        return Polynomial(res)
    def __sub__(self, o):
        res = defaultdict(Fraction, self.terms)
        for d, v in o.terms.items(): res[d] -= v
        return Polynomial(res)
    def __mul__(self, o):
        res = defaultdict(Fraction)
        for d1, v1 in self.terms.items():
            for d2, v2 in o.terms.items():
                res[d1 + d2] += v1 * v2
        return Polynomial(res)
    def degree(self):
        return max(self.terms.keys()) if self.terms else 0

def mod_inverse(a, m):
    m0, y, x = m, 0, 1
    if m == 1: return 0
    while a > 1:
        q = a // m
        t = m
        m = a % m
        a = t
        t = y
        y = x - q * y
        x = t
    return x + m0 if x < 0 else x

class Solver:
    def __init__(self):
        self.prec = {'+':1,'-':1,'*':2,'/':2,'^':3}
    def _tokenize(self, expr):
        expr = expr.replace(' ','').replace('**','^').replace('\\times','*').replace('\\cdot','*')
        expr = re.sub(r'(\d)(x)', r'\1*\2', expr)
        return re.findall(r'\d+\.\d+|\d+|x|[\+\-\*\/\(\)\^]', expr)
    def _parse(self, tokens):
        ops, values = [], []
        def apply():
            if len(values) < 2: return
            op = ops.pop()
            r,l = values.pop(), values.pop()
            if op=='+': values.append(l+r)
            elif op=='-': values.append(l-r)
            elif op=='*': values.append(l*r)
            elif op=='/': values.append(l*(Polynomial({0:1})/r if r.degree()==0 else Polynomial({0:0})))
        for i,t in enumerate(tokens):
            if t=='(': ops.append(t)
            elif t==')':
                while ops and ops[-1]!='(': apply()
                ops.pop()
            elif t in self.prec:
                if t=='-' and (i==0 or tokens[i-1] in '(+-*/'):
                    values.append(Polynomial({0:0}))
                while ops and ops[-1]!='(' and self.prec.get(ops[-1],0)>=self.prec[t]: apply()
                ops.append(t)
            elif t=='x': values.append(Polynomial({1:1}))
            else: values.append(Polynomial({0:Fraction(t)}))
        while ops: apply()
        return values[0] if values else Polynomial({0:0})
    def solve(self, problem):
        try:
            mod_match = re.search(r'mod(?:ulo)?\s*(\d+)', problem, re.I)
            mod_val = int(mod_match.group(1)) if mod_match else None
            clean = re.sub(r'\\\(|\\\)|\\\[|\\\]|\$|Solve|for x|What is','',problem,flags=re.I)
            if '=' in clean:
                lhs,rhs = clean.split('=')
                poly = self._parse(self._tokenize(lhs)) - self._parse(self._tokenize(rhs))
                deg = poly.degree()
                if deg==1:
                    a,b = poly.terms[1], poly.terms[0]
                    ans = -b/a
                    if mod_val: return (int(-b.numerator)*mod_inverse(int(a.numerator),mod_val))%mod_val
                elif deg==2:
                    a,b,c = poly.terms[2], poly.terms[1], poly.terms[0]
                    disc = b*b - 4*a*c
                    root_disc = math.isqrt(int(disc))
                    ans = (-b + root_disc)/(2*a)
                else: ans=0
            else:
                ans = self._parse(self._tokenize(clean)).terms[0]
            return int(ans) if isinstance(ans,Fraction) and ans.denominator==1 else str(ans)
        except: return 0

def solve(problem:str): return Solver().solve(problem)
# === AIMO-3 EXTENSION PLACEHOLDER ===
# CRT_SOLVER: Chinese Remainder Theorem (deterministic, exact)
# PRIME_FACTORIZATION: integer-only, sqrt(n) bounded
# GEOMETRY_ANALYTIC: exact coordinate geometry
