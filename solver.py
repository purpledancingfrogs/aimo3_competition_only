from fractions import Fraction
import re

def solve(problem):
    if not isinstance(problem, str):
        return 0
    s = problem
    s = re.sub(r'\\\(|\\\)|\\\[|\\\]|\$', '', s)
    s = re.sub(r'(?i)solve|for x\.?|what is', '', s)
    s = s.replace('\\times','*').replace('\\cdot','*').replace('\u2212','-')
    s = s.replace(' ', '').rstrip('.?!')
    s = re.sub(r'(\d)(x)', r'\1*\2', s)

    def eval_expr(e):
        tokens = re.findall(r'\d+|x|[+\-*/()]', e)
        ops, vals = [], []
        prec = {'+':1,'-':1,'*':2,'/':2}

        def apply():
            op = ops.pop()
            b = vals.pop()
            a = vals.pop()
            if op == '+': vals.append((a[0]+b[0], a[1]+b[1]))
            if op == '-': vals.append((a[0]-b[0], a[1]-b[1]))
            if op == '*':
                if a[0] != 0 and b[0] != 0: vals.append((0,0))
                else: vals.append((a[0]*b[1]+b[0]*a[1], a[1]*b[1]))
            if op == '/':
                if b[0] != 0: vals.append((0,0))
                else: vals.append((a[0]/b[1], a[1]/b[1]))

        for t in tokens:
            if t.isdigit():
                vals.append((Fraction(0), Fraction(t)))
            elif t == 'x':
                vals.append((Fraction(1), Fraction(0)))
            elif t == '(':
                ops.append(t)
            elif t == ')':
                while ops and ops[-1] != '(':
                    apply()
                ops.pop()
            else:
                while ops and ops[-1] != '(' and prec.get(ops[-1],0) >= prec[t]:
                    apply()
                ops.append(t)
        while ops:
            apply()
        return vals[0]

    if '=' in s:
        l,r = s.split('=')
        a1,b1 = eval_expr(l)
        a2,b2 = eval_expr(r)
        if a1 == a2:
            return 0
        res = (b2-b1)/(a1-a2)
    else:
        res = eval_expr(s)[1]

    return int(res) if res.denominator == 1 else f"{res.numerator}/{res.denominator}"
