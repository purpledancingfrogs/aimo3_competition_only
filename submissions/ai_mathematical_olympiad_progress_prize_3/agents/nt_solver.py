import re
from sympy import symbols, Eq, solve
from sympy.ntheory import isprime
from sympy import factorint

class NTSolver:
    def solve(self, problem_text):
        t = problem_text.lower().replace("\\times", "*").replace("$", "")
        t = re.sub(r"[?]", "", t)

        # simple arithmetic
        try:
            m = re.search(r'(-?\d+)\s*([+\-*/])\s*(-?\d+)', t)
            if m:
                return eval(m.group(0))
        except:
            pass

        # linear equations like 4x=4
        if "x" in t and "=" in t:
            x = symbols("x")
            lhs, rhs = t.split("=")
            lhs = re.sub(r'(\d)(x)', r'\1*\2', lhs)
            rhs = re.sub(r'(\d)(x)', r'\1*\2', rhs)
            try:
                sol = solve(Eq(eval(lhs), eval(rhs)), x)
                if sol:
                    return int(sol[0])
            except:
                pass

        # multiplication phrasing
        nums = re.findall(r'-?\d+', t)
        if "times" in t and len(nums) == 2:
            return int(nums[0]) * int(nums[1])

        # prime check
        if "prime" in t and nums:
            return int(isprime(int(nums[0])))

        # factorization
        if "factor" in t and nums:
            return factorint(int(nums[0]))

        return None
