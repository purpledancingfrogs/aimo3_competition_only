import re
from fractions import Fraction

def solve(problem):
    def normalize(s):
        s = re.sub(r'\\\(|\\\)|\\\[|\\\]|\$', '', s)
        s = re.sub(r'(?i)solve|for x\.?|what is', '', s)
        s = s.replace('\\times','*').replace('\\cdot','*').replace('\u2212','-')
        s = s.replace(' ','').rstrip('.?!')
        s = re.sub(r'(\d)(x)', r'\1*x', s, flags=re.I)
        return s

    def eval_expr(expr):
        tokens = re.findall(r'\d+|\d+/\d+|x|[+\-*/()]', expr)
        vals, ops = [], []
        prec = {'+':1,'-':1,'*':2,'/':2}

        def apply():
            if len(vals) < 2 or not ops:
                return
            b = vals.pop()
            a = vals.pop()
            op = ops.pop()
            if op == '+': vals.append((a[0]+b[0], a[1]+b[1]))
            elif op == '-': vals.append((a[0]-b[0], a[1]-b[1]))
            elif op == '*':
                if a[0]!=0 and b[0]!=0: vals.append((0,0))
                else: vals.append((a[0]*b[1]+b[0]*a[1], a[1]*b[1]))
            elif op == '/':
                if b[0]!=0 or b[1]==0: vals.append((0,0))
                else: vals.append((a[0]/b[1], a[1]/b[1]))

        i=0
        while i < len(tokens):
            t = tokens[i]
            if t == '(':
                ops.append(t)
            elif t == ')':
                while ops and ops[-1] != '(':
                    apply()
                if ops: ops.pop()
            elif t in '+-*/':
                if t=='-' and (i==0 or tokens[i-1] in '+-*/('):
                    vals.append((Fraction(0),Fraction(0)))
                while ops and ops[-1]!='(' and prec.get(ops[-1],0)>=prec[t]:
                    apply()
                ops.append(t)
            elif t.lower()=='x':
                vals.append((Fraction(1),Fraction(0)))
            else:
                vals.append((Fraction(0),Fraction(t)))
            i+=1
        while ops:
            apply()
        return vals[0] if vals else (Fraction(0),Fraction(0))

    try:
        clean = normalize(problem)
        if '=' in clean:
            l,r = clean.split('=')
            a1,b1 = eval_expr(l)
            a2,b2 = eval_expr(r)
            A = a1-a2
            B = b2-b1
            if A==0: return 0
            res = B/A
        else:
            _,res = eval_expr(clean)
        return int(res) if res.denominator==1 else f"{res.numerator}/{res.denominator}"
    except:
        return 0
