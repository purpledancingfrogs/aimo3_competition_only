import sys
import re
from z3 import Int, Solver, Optimize, sat
from sympy import symbols, sympify
from itertools import product

MODS = [2,3,5,7,11]

# ---------------- ROUTER ----------------
def route(expr: str) -> str:
    e = expr.lower()
    if re.search(r'(min|max|least|greatest|largest|smallest|mod|remainder|divisible|distinct)', e):
        return "Z3"
    if re.search(r'(area|volume|circle|triangle|distance|midpoint|intersection|polynomial|root)', e):
        return "SYMPY"
    return "Z3"

# ---------------- Z3 ENGINE ----------------
def solve_z3(expr: str):
    text = expr.lower()
    optimize_mode = None
    if re.search(r'(min|least|smallest)', text):
        optimize_mode = "min"
    if re.search(r'(max|greatest|largest)', text):
        optimize_mode = "max"

    expr = expr.replace("=", "<=").replace("=", ">=").replace(" ", "")
    vars_found = sorted(set(re.findall(r'[a-z]', expr)))
    if not vars_found:
        return None

    z3_vars = {v: Int(v) for v in vars_found}
    s = Optimize() if optimize_mode else Solver()

    for v in z3_vars.values():
        s.add(v >= -10000, v <= 10000)

    parts = re.split(r',|and', expr)
    for p in parts:
        if '==' in p:
            l,r = p.split('=='); s.add(eval(l,{},z3_vars)==eval(r,{},z3_vars))
        elif '=' in p:
            l,r = p.split('='); s.add(eval(l,{},z3_vars)==eval(r,{},z3_vars))
        elif '<=' in p:
            l,r = p.split('<='); s.add(eval(l,{},z3_vars)<=eval(r,{},z3_vars))
        elif '>=' in p:
            l,r = p.split('>='); s.add(eval(l,{},z3_vars)>=eval(r,{},z3_vars))
        elif '<' in p:
            l,r = p.split('<'); s.add(eval(l,{},z3_vars)<eval(r,{},z3_vars))
        elif '>' in p:
            l,r = p.split('>'); s.add(eval(l,{},z3_vars)>eval(r,{},z3_vars))

    if optimize_mode:
        target = next(iter(z3_vars.values()))
        s.minimize(target) if optimize_mode=="min" else s.maximize(target)

    if s.check()!=sat:
        return None

    m = s.model()
    if len(z3_vars)==1:
        return m[next(iter(z3_vars.values()))].as_long()
    return sum(m[v].as_long() for v in z3_vars.values())

# ---------------- SYMPY ----------------
def solve_sympy(expr: str):
    try:
        sol = sympify(expr).solve()
        if sol:
            return int(sol[0])
    except Exception:
        pass
    return None

# ---------------- BRUTE (BOUNDED) ----------------
def solve_brute(expr: str, limit=200):
    vars_found = sorted(set(re.findall(r'[a-z]', expr)))
    if len(vars_found)>2:
        return None
    env = {}
    for vals in product(range(-limit,limit+1), repeat=len(vars_found)):
        for v,val in zip(vars_found,vals):
            env[v]=val
        try:
            if eval(expr.replace('=','=='),{},env):
                return sum(env.values())
        except Exception:
            pass
    return None

# ---------------- META VERIFIER ----------------
def meta_verify(candidates):
    if not candidates:
        return None
    for c in candidates:
        if all(c % m == candidates[0] % m for m in MODS):
            return c
    return candidates[0]

# ---------------- MAIN ----------------
def main():
    if len(sys.argv)<2:
        return

    expr = " ".join(sys.argv[1:])
    candidates = []

    z3_ans = solve_z3(expr)
    if z3_ans is not None:
        candidates.append(z3_ans)

    sym_ans = solve_sympy(expr)
    if sym_ans is not None:
        candidates.append(sym_ans)

    brute_ans = solve_brute(expr)
    if brute_ans is not None:
        candidates.append(brute_ans)

    final = meta_verify(candidates)
    print(0 if final is None else final%1000)

if __name__=="__main__":
    main()
