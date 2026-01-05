import sys
import re
from z3 import Int, Solver, Optimize, sat

PRIMES = (2,3,5,7,11)

def norm1000(x: int) -> int:
    x %= 1000
    return x if x >= 0 else (x + 1000) % 1000

def route(expr: str) -> str:
    e = expr.lower()
    if re.search(r'(mod|remainder|divisible|distinct|min|max|least|greatest|largest|smallest)', e):
        return "Z3"
    if re.search(r'(area|volume|circle|triangle|distance|midpoint|intersection|polynomial|root)', e):
        return "SYMPY"
    return "Z3"

def solve_z3(expr: str):
    text = expr.lower()
    optimize = None
    if re.search(r'(min|least|smallest)', text): optimize = "min"
    if re.search(r'(max|greatest|largest)', text): optimize = "max"

    s = expr.replace("=","<=").replace("=",">=").replace(" ", "")
    vars_found = sorted(set(re.findall(r'[a-z]', s)))
    if not vars_found:
        return None

    V = {v: Int(v) for v in vars_found}
    opt = Optimize() if optimize else Solver()

    # bounds
    for v in V.values():
        opt.add(v >= -20000, v <= 20000)

    # distinct
    if "distinct" in text:
        opt.add(*[V[v] for v in vars_found])

    # constraints
    parts = re.split(r',|and', s)
    for p in parts:
        if "mod" in p:
            # x mod k = r
            m = re.search(r'([a-z])mod(\d+)=([0-9]+)', p)
            if m:
                v,k,r = m.groups()
                opt.add(V[v] % int(k) == int(r))
        elif "divisible" in p:
            m = re.search(r'([a-z])divisibleby(\d+)', p)
            if m:
                v,k = m.groups()
                opt.add(V[v] % int(k) == 0)
        elif "==" in p:
            l,r = p.split("=="); opt.add(eval(l,{},V)==eval(r,{},V))
        elif "=" in p:
            l,r = p.split("=");  opt.add(eval(l,{},V)==eval(r,{},V))
        elif "<=" in p:
            l,r = p.split("<="); opt.add(eval(l,{},V)<=eval(r,{},V))
        elif ">=" in p:
            l,r = p.split(">="); opt.add(eval(l,{},V)>=eval(r,{},V))
        elif "<" in p:
            l,r = p.split("<");  opt.add(eval(l,{},V)< eval(r,{},V))
        elif ">" in p:
            l,r = p.split(">");  opt.add(eval(l,{},V)> eval(r,{},V))

    if optimize:
        tgt = V[vars_found[0]]
        opt.minimize(tgt) if optimize=="min" else opt.maximize(tgt)

    if opt.check() != sat:
        return None

    m = opt.model()
    if len(V)==1:
        return m[next(iter(V.values()))].as_long()
    return sum(m[v].as_long() for v in V.values())

def main():
    if len(sys.argv)<2: return
    expr=" ".join(sys.argv[1:])
    ans = solve_z3(expr) if route(expr)=="Z3" else None
    print(0 if ans is None else norm1000(int(ans)))

if __name__=="__main__":
    main()
