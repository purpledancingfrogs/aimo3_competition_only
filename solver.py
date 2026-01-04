import sys
import re
import math
from fractions import Fraction

def nCr(n, r):
    if r < 0 or r > n: return 0
    return math.factorial(n) // (math.factorial(r) * math.factorial(n - r))

def clean_problem(p):
    p = p.replace('$','').replace('\\times','*').replace('×','*').replace('\\cdot','*')
    p = p.replace('=', '==')
    p = re.sub(r'(?i)what is|solve|for x|for \$x\$|\.', '', p).strip()
    return p

def solve(problem):
    p = clean_problem(problem)
    try:
        if 'choose' in p.lower():
            nums = list(map(int, re.findall(r'\d+', p)))
            if len(nums) >= 2:
                return str(nCr(max(nums), min(nums)))

        if 'distance' in p.lower():
            nums = list(map(int, re.findall(r'-?\d+', p)))
            if len(nums) >= 4:
                x1,y1,x2,y2 = nums[:4]
                return str((x1-x2)**2 + (y1-y2)**2)

        if 'x' in p and '==' in p:
            lhs, rhs = p.split('==')
            res = eval(f"({lhs})-({rhs})", {"__builtins__":None}, {"x":1j})
            if res.imag != 0:
                ans = Fraction(-res.real/res.imag).limit_denominator()
                return str(int(ans) if ans.denominator==1 else ans)

        arith = re.sub(r'[a-zA-Z]', '', p)
        if re.search(r'\d', arith):
            r = eval(arith, {"__builtins__":None}, {})
            return str(int(r) if r==int(r) else r)
    except:
        pass
    return "0"

if __name__ == "__main__":
    for line in sys.stdin:
        if line.strip():
            print(solve(line.strip()))
