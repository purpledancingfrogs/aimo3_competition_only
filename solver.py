import re
import unicodedata

from sympy import symbols, Eq, solve as sp_solve, sympify, gcd as sp_gcd, nextprime, diff
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

_X = symbols("x")
_TRANS = standard_transformations + (implicit_multiplication_application,)

def _norm(s: str) -> str:
    s = "" if s is None else str(s)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u200b","").replace("\u200c","").replace("\u200d","")
    s = s.replace("×","*").replace("÷","/").replace("^","**")
    return s.strip()

def _strip_instructions(t: str) -> str:
    t = t.lower()
    for w in [
        "return final integer only", "return integer only",
        "return final integer", "return the final integer",
        "return", "final", "integer only"
    ]:
        t = t.replace(w, " ")
    t = t.replace("?", " ").replace(";", " ").replace(",", " ").replace(":", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t

def solve_problem(problem_str: str) -> str:
    text0 = _norm(problem_str)
    text = _strip_instructions(text0)

    try:
        # TYPE A: prime greater than N
        if "prime" in text and "greater than" in text:
            nums = [int(x) for x in re.findall(r"\d+", text)]
            return str(int(nextprime(nums[-1]))) if nums else "0"

        # TYPE B: gcd(a,b)
        if "gcd" in text:
            nums = [int(x) for x in re.findall(r"\d+", text)]
            return str(int(sp_gcd(nums[0], nums[1]))) if len(nums) >= 2 else "0"

        # TYPE C: modular arithmetic
        if re.search(r"\bmod\b", text):
            text = re.sub(r"\bmod\b", "%", text)

        # TYPE D: minimize(expr) -> argmin x (derivative=0)
        if "minimize" in text:
            expr_str = text.replace("minimize", " ").strip()
            expr = sympify(expr_str)
            crit = sp_solve(diff(expr, _X), _X)
            if crit:
                v = crit[0]
                try:
                    return str(int(v))
                except Exception:
                    return str(int(sympify(v)))
            return "0"

        # TYPE E: equation with '=' (robustly extract first equation substring)
        if "=" in text:
            m = re.search(r"([0-9x\-\+\*/%\(\)\.\s\*]+)=\s*([0-9x\-\+\*/%\(\)\.\s\*]+)", text)
            if m:
                lhs_s = m.group(1).strip().rstrip(".")
                rhs_s = m.group(2).strip().rstrip(".")
                lhs = parse_expr(lhs_s, transformations=_TRANS)
                rhs = parse_expr(rhs_s, transformations=_TRANS)
                sol = sp_solve(Eq(lhs, rhs), _X)
                if sol:
                    v = sol[0]
                    try:
                        return str(int(v))
                    except Exception:
                        return str(int(sympify(v)))
                return "0"

        # TYPE F: arithmetic
        t = text
        t = t.replace("what is", " ").replace("evaluate", " ").replace("solve", " ")
        t = t.replace("times", "*").replace("divided by", "/")
        t = re.sub(r"\s+", " ", t).strip()

        allowed = set("0123456789+-*/%(). **")
        cleaned = "".join([c for c in t if c in allowed]).strip()
        if cleaned:
            return str(int(sympify(cleaned)))

    except Exception:
        pass

    nums = re.findall(r"\d+", text)
    return nums[-1] if nums else "0"

def solve(prompt):
    return solve_problem(prompt)

def predict(problems):
    if isinstance(problems, (list, tuple)):
        return [solve_problem(p) for p in problems]
    return [solve_problem(problems)]