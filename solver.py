import re
from fractions import Fraction

def solve(problem: str):
    if not isinstance(problem, str):
        return 0

    s = problem.lower()
    s = re.sub(r'\\\(|\\\)|\\\[|\\\]|\$', '', s)
    s = re.sub(r'solve|what is|for x', '', s)
    s = s.replace(' ', '').rstrip('.?')
    s = s.replace('\\times', '*').replace('\\cdot', '*')

    def eval_expr(expr):
        expr = re.sub(r'(\d)(x)', r'\1*x', expr)
        tokens = re.findall(r'\d+|x|[+\-*/()]', expr)

        def parse(tokens):
            vals, ops = [], []

            def apply():
                b = vals.pop()
                a = vals.pop()
                op = ops.pop()
                if op == '+': vals.append(a + b)
                elif op == '-': vals.append(a - b)
                elif op == '*': vals.append(a * b)
                elif op == '/': vals.append(a / b if b != 0 else Fraction(0))

            i = 0
            while i < len(tokens):
                t = tokens[i]
                if t.isdigit():
                    vals.append(Fraction(int(t)))
                elif t == 'x':
                    vals.append(('x', Fraction(1)))
                elif t in '+-*/':
                    while ops and ops[-1] in '*/' and t in '+-':
                        apply()
                    ops.append(t)
                elif t == '(':
                    ops.append(t)
                elif t == ')':
                    while ops and ops[-1] != '(':
                        apply()
                    ops.pop()
                i += 1

            while ops:
                apply()
            return vals[0]

        return parse(tokens)

    if '=' in s:
        left, right = s.split('=')
        a1, b1 = 0, eval_expr(left)
        a2, b2 = 0, eval_expr(right)
        if isinstance(b1, tuple): a1, b1 = b1[1], 0
        if isinstance(b2, tuple): a2, b2 = b2[1], 0
        if a1 == a2:
            return 0
        res = Fraction(b2 - b1, a1 - a2)
    else:
        val = eval_expr(s)
        res = val[1] if isinstance(val, tuple) else val

    return int(res) if res.denominator == 1 else f"{res.numerator}/{res.denominator}"
