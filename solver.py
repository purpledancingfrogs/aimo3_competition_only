import sys
import re
from z3 import Int, Solver, Optimize, sat
from itertools import product

PRIMES = (2,3,5,7,11)

def norm1000(x: int) -> int:
    x %= 1000
    return x if x >= 0 else (x + 1000) % 1000

def route(expr: str) -> str:
    e = expr.lower()
    if re.search(r'(mod|remainder|divisible|distinct|min|max|least|greatest|largest|smallest)', e):
        return "Z3"
    if re.search(r'(area|volume|circle|triangle|distance|midpoint|intersection|polynomial|root|derivative|integral)', e):
        return "SYMPY"
    return "Z3"

def parse_constraints(expr: str):
    s = expr.replace("=","<=").replace("=",">=").replace(" ", "")
    return [p for p in re.split(r',|and', s) if p]

def solve_z3(expr: str):
    text = expr.lower()
    opt_mode = "min" if re.search(r'(min|least|smallest)', text) else "max" if re.search(r'(max|greatest|largest)', text) else None

    raw = expr.replace("=","<=").replace("=",">=").replace(" ", "")
    vars_found = sorted(set(re.findall(r'[a-z]', raw)))
    if not vars_found:
        return None

    V = {v: Int(v) for v in vars_found}
    S = Optimize() if opt_mode else Solver()

    for v in V.values():
        S.add(v >= -20000, v <= 20000)

    if "distinct" in text:
        S.add(*[V[v] for v in vars_found])

    for p in parse_constraints(expr):
        if "mod" in p:
            m = re.search(r'([a-z])mod(\d+)=([0-9]+)', p)
            if m:
                v,k,r = m.groups()
                S.add(V[v] % int(k) == int(r))
        elif "divisible" in p:
            m = re.search(r'([a-z])divisibleby(\d+)', p)
            if m:
                v,k = m.groups()
                S.add(V[v] % int(k) == 0)
        elif '==' in p:
            l,r = p.split('=='); S.add(eval(l,{},V)==eval(r,{},V))
        elif '=' in p:
            l,r = p.split('=');  S.add(eval(l,{},V)==eval(r,{},V))
        elif '<=' in p:
            l,r = p.split('<='); S.add(eval(l,{},V)<=eval(r,{},V))
        elif '>=' in p:
            l,r = p.split('>='); S.add(eval(l,{},V)>=eval(r,{},V))
        elif '<' in p:
            l,r = p.split('<');  S.add(eval(l,{},V)< eval(r,{},V))
        elif '>' in p:
            l,r = p.split('>');  S.add(eval(l,{},V)> eval(r,{},V))

    if opt_mode:
        tgt = V[vars_found[0]]
        (S.minimize if opt_mode=="min" else S.maximize)(tgt)

    if S.check() != sat:
        return None

    m = S.model()
    if len(V)==1:
        return m[next(iter(V.values()))].as_long()
    return sum(m[v].as_long() for v in V.values())

def brute_verify(expr: str, cand: int, limit=200000):
    # bounded enumeration around candidate using small window
    raw = expr.replace("=","<=").replace("=",">=").replace(" ", "")
    vars_found = sorted(set(re.findall(r'[a-z]', raw)))
    if len(vars_found)!=1:
        return True
    v = vars_found[0]
    for x in range(cand-500, cand+501):
        if x < -limit or x > limit: continue
        env = {v:x}
        ok = True
        for p in parse_constraints(expr):
            try:
                if '==' in p:
                    l,r=p.split('=='); ok &= (eval(l,{},env)==eval(r,{},env))
                elif '=' in p:
                    l,r=p.split('=');  ok &= (eval(l,{},env)==eval(r,{},env))
                elif '<=' in p:
                    l,r=p.split('<='); ok &= (eval(l,{},env)<=eval(r,{},env))
                elif '>=' in p:
                    l,r=p.split('>='); ok &= (eval(l,{},env)>=eval(r,{},env))
                elif '<' in p:
                    l,r=p.split('<');  ok &= (eval(l,{},env)< eval(r,{},env))
                elif '>' in p:
                    l,r=p.split('>');  ok &= (eval(l,{},env)> eval(r,{},env))
            except Exception:
                ok=False
            if not ok: break
        if ok and x!=cand:
            return False
    return True

def mod_guard(ans: int):
    return tuple(ans % p for p in PRIMES)

def main():
    if len(sys.argv)<2: return
    expr=" ".join(sys.argv[1:])
    ans = solve_z3(expr) if route(expr)=="Z3" else None
    if ans is None:
        print(0); return

    # Meta-verifier
    base_mod = mod_guard(ans)
    if not brute_verify(expr, ans):
        print(0); return

    print(norm1000(int(ans)))

if __name__=="__main__":
    main()
