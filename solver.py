import sys
import re
from z3 import Int, Solver, Optimize, sat
from sympy import symbols, Eq, solve
from math import isclose

PRIMES = (2,3,5,7,11)

def norm1000(x: int) -> int:
    x %= 1000
    return x if x >= 0 else (x + 1000) % 1000

def route(expr: str) -> str:
    e = expr.lower()
    if re.search(r'(circle|triangle|distance|midpoint|collinear|intersection|area)', e):
        return "GEOM"
    if re.search(r'(mod|remainder|divisible|distinct|min|max|least|greatest|largest|smallest)', e):
        return "Z3"
    return "Z3"

# ---------------- GEOMETRY (COORDINATE-ONLY, SAFE) ----------------
def solve_geometry(expr: str):
    # Minimal deterministic geometry layer:
    # supports distance, midpoint, collinearity via coordinates
    try:
        # Example canonical forms expected after translation:
        # distance((x1,y1),(x2,y2)) = k
        # midpoint((x1,y1),(x2,y2)) = (a,b)
        # collinear((x1,y1),(x2,y2),(x3,y3))
        # NOTE: LLM translation responsibility — this engine executes only

        # Extract all coordinates
        pts = re.findall(r'\((\-?\d+),(\-?\d+)\)', expr)
        pts = [(int(a), int(b)) for a,b in pts]

        if "distance" in expr:
            m = re.search(r'distance\(\((\-?\d+),(\-?\d+)\),\((\-?\d+),(\-?\d+)\)\)=([\-]?\d+)', expr)
            if not m:
                return None
            x1,y1,x2,y2,k = map(int, m.groups())
            return int((x1-x2)**2 + (y1-y2)**2 == k*k)

        if "midpoint" in expr:
            m = re.search(r'midpoint\(\((\-?\d+),(\-?\d+)\),\((\-?\d+),(\-?\d+)\)\)=\((\-?\d+),(\-?\d+)\)', expr)
            if not m:
                return None
            x1,y1,x2,y2,a,b = map(int, m.groups())
            return int((x1+x2)==2*a and (y1+y2)==2*b)

        if "collinear" in expr:
            m = re.findall(r'\((\-?\d+),(\-?\d+)\)', expr)
            if len(m)!=3:
                return None
            (x1,y1),(x2,y2),(x3,y3) = [(int(a),int(b)) for a,b in m]
            return int((x2-x1)*(y3-y1) == (x3-x1)*(y2-y1))

    except Exception:
        return None

    return None

# ---------------- Z3 CORE ----------------
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

    parts = re.split(r',|and', raw)
    for p in parts:
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

# ---------------- MAIN ----------------
def main():
    if len(sys.argv)<2: return
    expr=" ".join(sys.argv[1:])
    branch = route(expr)

    if branch=="GEOM":
        ans = solve_geometry(expr)
    else:
        ans = solve_z3(expr)

    print(0 if ans is None else norm1000(int(ans)))

if __name__=="__main__":
    main()
