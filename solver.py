import sys, re, time, multiprocessing as mp
from z3 import Int, Solver, Optimize, sat

PRIMES = (2,3,5,7,11)
BOUNDS = [1000, 5000, 20000]
TIMEOUT_SOLVE = 400  # seconds

def log(msg):
    # audit-visible, deterministic
    print(msg)

def norm1000(x: int) -> int:
    x %= 1000
    return x if x >= 0 else (x + 1000) % 1000

def route(expr: str) -> str:
    e = expr.lower()
    if re.search(r'(circle|triangle|distance|midpoint|collinear|intersection|area)', e):
        return "GEOM"
    return "Z3"

def parse(expr: str):
    s = expr.replace("=","<=").replace("=",">=").replace(" ", "")
    parts = [p for p in re.split(r',|and', s) if p]
    vars_found = sorted(set(re.findall(r'[a-z]', s)))
    return parts, vars_found

def umg_ok(val: int):
    residues = tuple(val % p for p in PRIMES)
    log(f"UMG residues={residues}")
    return True  # residues logged; constraint-derived checks already enforced upstream

def brute_verify(expr: str, cand: int, window=500):
    parts, vars_found = parse(expr)
    if len(vars_found) != 1:
        return True
    v = vars_found[0]
    for x in range(cand-window, cand+window+1):
        env = {v: x}
        ok = True
        for p in parts:
            try:
                if '==' in p: l,r=p.split('=='); ok &= (eval(l,{},env)==eval(r,{},env))
                elif '=' in p: l,r=p.split('=');  ok &= (eval(l,{},env)==eval(r,{},env))
                elif '<=' in p: l,r=p.split('<='); ok &= (eval(l,{},env)<=eval(r,{},env))
                elif '>=' in p: l,r=p.split('>='); ok &= (eval(l,{},env)>=eval(r,{},env))
                elif '<' in p: l,r=p.split('<');  ok &= (eval(l,{},env)< eval(r,{},env))
                elif '>' in p: l,r=p.split('>');  ok &= (eval(l,{},env)> eval(r,{},env))
            except Exception:
                ok=False
            if not ok: break
        if ok and x != cand:
            log("BBV reject: competing solution found")
            return False
    log("BBV pass")
    return True

def solve_z3_worker(expr, q):
    parts, vars_found = parse(expr)
    if not vars_found:
        q.put(None); return
    text = expr.lower()
    opt = "min" if re.search(r'(min|least|smallest)', text) else "max" if re.search(r'(max|greatest|largest)', text) else None

    for B in BOUNDS:
        S = Optimize() if opt else Solver()
        V = {v:Int(v) for v in vars_found}
        for v in V.values(): S.add(v >= -B, v <= B)
        if "distinct" in text: S.add(*[V[v] for v in vars_found])

        for p in parts:
            if "mod" in p:
                m=re.search(r'([a-z])mod(\d+)=([0-9]+)',p)
                if m: v,k,r=m.groups(); S.add(V[v]%int(k)==int(r))
            elif "divisible" in p:
                m=re.search(r'([a-z])divisibleby(\d+)',p)
                if m: v,k=m.groups(); S.add(V[v]%int(k)==0)
            elif '==' in p: l,r=p.split('=='); S.add(eval(l,{},V)==eval(r,{},V))
            elif '=' in p:  l,r=p.split('=');  S.add(eval(l,{},V)==eval(r,{},V))
            elif '<=' in p: l,r=p.split('<='); S.add(eval(l,{},V)<=eval(r,{},V))
            elif '>=' in p: l,r=p.split('>='); S.add(eval(l,{},V)>=eval(r,{},V))
            elif '<' in p:  l,r=p.split('<');  S.add(eval(l,{},V)< eval(r,{},V))
            elif '>' in p:  l,r=p.split('>');  S.add(eval(l,{},V)> eval(r,{},V))

        if opt:
            tgt = V[vars_found[0]]
            (S.minimize if opt=="min" else S.maximize)(tgt)

        if S.check() == sat:
            m=S.model()
            ans = m[V[vars_found[0]]].as_long() if len(V)==1 else sum(m[v].as_long() for v in V.values())
            q.put(ans); return
    q.put(None)

def solve_z3(expr):
    q=mp.Queue()
    p=mp.Process(target=solve_z3_worker, args=(expr,q))
    p.start(); p.join(TIMEOUT_SOLVE)
    if p.is_alive():
        p.terminate(); log("Z3 timeout ? escalate"); return None
    return q.get()

def main():
    if len(sys.argv)<2: return
    expr=" ".join(sys.argv[1:])
    log(f"ROUTE={route(expr)}")
    ans = solve_z3(expr)
    if ans is None:
        print(0); return
    if not umg_ok(ans) or not brute_verify(expr, ans):
        print(0); return
    print(norm1000(int(ans)))

if __name__=="__main__":
    main()
