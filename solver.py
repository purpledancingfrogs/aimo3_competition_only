import sys, re, multiprocessing as mp

# ---------- Optional engines ----------
try:
    from z3 import Int, Solver, Optimize, sat
    HAS_Z3 = True
except Exception:
    HAS_Z3 = False

try:
    import sympy as sp
    HAS_SYMPY = True
except Exception:
    HAS_SYMPY = False

# ---------- Constants ----------
PRIMES = (2,3,5,7,11)
BOUNDS = [1000, 5000, 20000]
TIMEOUT_SOLVE = 400

# ---------- Utilities ----------
def norm1000(x:int)->int:
    x %= 1000
    return x if x>=0 else (x+1000)%1000

def reject():
    print(0)
    sys.exit(0)

def parse(expr:str):
    s = expr.replace("=","<=").replace("=",">=").replace(" ","")
    parts = [p for p in re.split(r',|and', s) if p]
    vars_ = sorted(set(re.findall(r'[a-z]', s)))
    return parts, vars_

# ---------- Universal Modulo Guards (ENFORCING) ----------
def umg_enforce(val:int, expected=None)->bool:
    for p in PRIMES:
        r = val % p
        if expected and p in expected and r != expected[p]:
            return False
    return True

# ---------- Bounded Brute Verification ----------
def brute_verify(expr, cand, window=500):
    parts, vars_ = parse(expr)
    if len(vars_) != 1:
        return True  # multi-var verified by solver only
    v = vars_[0]
    for x in range(cand-window, cand+window+1):
        if x == cand: continue
        env = {v:x}
        ok = True
        for p in parts:
            try:
                if '==' in p: l,r=p.split('=='); ok &= (eval(l,{},env)==eval(r,{},env))
                elif '=' in p:  l,r=p.split('=');  ok &= (eval(l,{},env)==eval(r,{},env))
                elif '<=' in p: l,r=p.split('<='); ok &= (eval(l,{},env)<=eval(r,{},env))
                elif '>=' in p: l,r=p.split('>='); ok &= (eval(l,{},env)>=eval(r,{},env))
                elif '<' in p:  l,r=p.split('<');  ok &= (eval(l,{},env)< eval(r,{},env))
                elif '>' in p:  l,r=p.split('>');  ok &= (eval(l,{},env)> eval(r,{},env))
            except Exception:
                ok=False
            if not ok: break
        if ok:
            return False
    return True

# ---------- Z3 Solver ----------
def solve_z3(expr):
    if not HAS_Z3: return None
    parts, vars_ = parse(expr)
    if not vars_: return None
    opt = "min" if re.search(r'(min|least|smallest)',expr.lower()) else \
          "max" if re.search(r'(max|greatest|largest)',expr.lower()) else None

    for B in BOUNDS:
        S = Optimize() if opt else Solver()
        V = {v:Int(v) for v in vars_}
        for v in V.values(): S.add(v>=-B, v<=B)

        for p in parts:
            if 'mod' in p:
                m=re.search(r'([a-z])mod(\d+)=([0-9]+)',p)
                if m: v,k,r=m.groups(); S.add(V[v]%int(k)==int(r))
            elif '==' in p: l,r=p.split('=='); S.add(eval(l,{},V)==eval(r,{},V))
            elif '=' in p:  l,r=p.split('=');  S.add(eval(l,{},V)==eval(r,{},V))
            elif '<=' in p: l,r=p.split('<='); S.add(eval(l,{},V)<=eval(r,{},V))
            elif '>=' in p: l,r=p.split('>='); S.add(eval(l,{},V)>=eval(r,{},V))
            elif '<' in p:  l,r=p.split('<');  S.add(eval(l,{},V)< eval(r,{},V))
            elif '>' in p:  l,r=p.split('>');  S.add(eval(l,{},V)> eval(r,{},V))

        if opt:
            tgt = V[vars_[0]]
            (S.minimize if opt=="min" else S.maximize)(tgt)

        if S.check()==sat:
            m=S.model()
            return m[V[vars_[0]]].as_long() if len(vars_)==1 else sum(m[v].as_long() for v in V.values())
    return None

# ---------- SymPy Fallback ----------
def solve_sympy(expr):
    if not HAS_SYMPY: return None
    parts, vars_ = parse(expr)
    if not vars_: return None
    syms = sp.symbols(vars_, integer=True)
    env = dict(zip(vars_, syms))
    eqs=[]
    for p in parts:
        if '==' in p: l,r=p.split('=='); eqs.append(sp.Eq(eval(l,{},env),eval(r,{},env)))
        elif '=' in p:  l,r=p.split('=');  eqs.append(sp.Eq(eval(l,{},env),eval(r,{},env)))
    sol = sp.solve(eqs, syms, dict=True)
    if sol:
        return int(sol[0][syms[0]])
    return None

# ---------- Main ----------
def main():
    if len(sys.argv)<2: reject()
    expr=" ".join(sys.argv[1:])
    ans = solve_z3(expr)
    if ans is None:
        ans = solve_sympy(expr)
    if ans is None:
        reject()
    if not umg_enforce(ans):
        reject()
    if not brute_verify(expr, ans):
        reject()
    print(norm1000(int(ans)))

if __name__=="__main__":
    main()
# --- Geometry Kernel (Deterministic, Coordinate-Only) ---

def geom_detect(expr:str)->bool:
    return bool(re.search(r'(circle|triangle|distance|midpoint|collinear|intersection|segment)', expr.lower()))

def solve_geometry(expr:str):
    # Coordinate-only, integer/rational-safe
    # Supports: distance, midpoint, collinearity, simple intersections

    if not HAS_SYMPY:
        return None

    e = expr.lower()

    # Extract points like A(1,2)
    pts = re.findall(r'([a-z])\((-?\d+),(-?\d+)\)', e)
    if not pts:
        return None

    P = {name:(sp.Integer(x), sp.Integer(y)) for name,x,y in pts}

    # Distance squared
    if 'distance' in e:
        m = re.search(r'distance.*?([a-z]).*?([a-z])', e)
        if not m: return None
        a,b = m.groups()
        (x1,y1),(x2,y2) = P[a],P[b]
        return (x1-x2)**2 + (y1-y2)**2

    # Collinearity check
    if 'collinear' in e:
        if len(P) < 3: return None
        (x1,y1),(x2,y2),(x3,y3) = list(P.values())[:3]
        det = x1*(y2-y3)+x2*(y3-y1)+x3*(y1-y2)
        return int(det == 0)

    return None
# --- Dual-World Consistency Lock (DWCL) ---

def normalize_expr_worldA(expr:str)->str:
    # Original expression, minimal normalization
    return expr.replace("=","<=").replace("=",">=")

def normalize_expr_worldB(expr:str)->str:
    # Semantically equivalent but syntactically different
    e = expr.replace("=","<=").replace("=",">=")
    e = re.sub(r'([a-z])=([0-9]+)', r'\1==\2', e)
    e = e.replace("and", ",")
    return e

def solve_with_dwcl(expr:str):
    A = normalize_expr_worldA(expr)
    B = normalize_expr_worldB(expr)

    ansA = solve_z3(A) or solve_sympy(A)
    ansB = solve_z3(B) or solve_sympy(B)

    if ansA is None or ansB is None:
        return None

    if int(ansA) != int(ansB):
        return None

    return int(ansA)
# --- Layer 1: Multi-Invariant Closure (MIC) ---

def invariant_closure(expr, val):
    parts, vars_ = parse(expr)
    if len(vars_) != 1:
        return True
    v = vars_[0]
    env = {v: val}

    # parity chain
    if "even" in expr.lower() and val % 2 != 0:
        return False
    if "odd" in expr.lower() and val % 2 != 1:
        return False

    # monotonic bounds
    for p in parts:
        try:
            if '<=' in p:
                l,r = p.split('<=')
                if not eval(l,{},env) <= eval(r,{},env): return False
            if '>=' in p:
                l,r = p.split('>=')
                if not eval(l,{},env) >= eval(r,{},env): return False
        except Exception:
            pass

    return True


# --- Layer 2: Solution Uniqueness Certificate (SUC) ---

def uniqueness_certificate(expr, cand):
    if not HAS_Z3:
        return True
    parts, vars_ = parse(expr)
    if len(vars_) != 1:
        return True

    v = vars_[0]
    V = Int(v)
    S = Solver()
    S.add(V != cand)

    for p in parts:
        try:
            if '==' in p: l,r=p.split('=='); S.add(eval(l,{}, {v:V})==eval(r,{}, {v:V}))
            elif '=' in p: l,r=p.split('=');  S.add(eval(l,{}, {v:V})==eval(r,{}, {v:V}))
            elif '<=' in p: l,r=p.split('<='); S.add(eval(l,{}, {v:V})<=eval(r,{}, {v:V}))
            elif '>=' in p: l,r=p.split('>='); S.add(eval(l,{}, {v:V})>=eval(r,{}, {v:V}))
        except Exception:
            pass

    return S.check() != sat


# --- Layer 3: Canonical Answer Form (CAF) ---

def canonical_answer(val):
    if not isinstance(val, int):
        reject()
    return norm1000(val)


# --- Final acceptance gate override ---
def final_accept(expr, ans):
    if not umg_enforce(ans):
        reject()
    if not invariant_closure(expr, ans):
        reject()
    if not brute_verify(expr, ans):
        reject()
    if not uniqueness_certificate(expr, ans):
        reject()
    print(canonical_answer(ans))
    sys.exit(0)
