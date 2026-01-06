import re, math

PATH="solver.py"

def _append_patch(src: str) -> str:
    if "MPV7_PATCH_BEGIN" in src:
        print("ALREADY_PATCHED_MPV7")
        return src

    patch = r'''

# === MPV7_PATCH_BEGIN ===
import re as _re
import math as _math

# broader factorial digit-sum (tolerate punctuation, spaces, unicode)
_mpv7_re_fact_digitsum = _re.compile(r"(?:sum\s+of\s+digits\s+of)\s+(\d{1,7})\s*!\s*(?:[)\].,:;\"'\s]|$)", _re.I)

def _mpv7_fact_digitsum(n: int):
    # bounded to keep worst-case safe under selfplay
    if n < 0 or n > 12000:
        return None
    f = _math.factorial(n)
    return str(sum((ord(c)-48) for c in str(f)))

# robust system/equation parsing (handles: 7x, 6y, unicode dot, minus, times)
_mpv7_eq_find = _re.compile(r"([0-9a-zA-Z+\-*/().,\s·×−^]{1,160})=([0-9a-zA-Z+\-*/().,\s·×−^]{1,160})")

def _mpv7_norm(s: str) -> str:
    return (s.replace("\u00a0"," ")
             .replace("×","*")
             .replace("·","*")
             .replace("−","-")
             .replace("^","**"))

def _mpv7_try_sympy_linear_system(text: str):
    try:
        import sympy as sp
        from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
    except Exception:
        return None

    t = _mpv7_norm(text)
    if len(t) > 20000:
        return None

    eqs=[]
    for m in _mpv7_eq_find.finditer(t):
        L=m.group(1).strip()
        R=m.group(2).strip()
        if not L or not R:
            continue
        if len(L) > 160 or len(R) > 160:
            continue
        # allow only safe chars after normalization
        if not _re.fullmatch(r"[0-9a-zA-Z+\-*/().,\s]+", L):
            continue
        if not _re.fullmatch(r"[0-9a-zA-Z+\-*/().,\s]+", R):
            continue
        eqs.append((L,R))
    if not eqs:
        return None
    if len(eqs) > 8:
        eqs = eqs[:8]

    # vars: detect x,y,z,a,b,c (bound to 3 vars max for safety)
    vars=set()
    for L,R in eqs:
        for v in ("x","y","z","a","b","c"):
            if _re.search(rf"(?<![A-Za-z0-9_]){v}(?![A-Za-z0-9_])", L) or _re.search(rf"(?<![A-Za-z0-9_]){v}(?![A-Za-z0-9_])", R):
                vars.add(v)
    if not vars:
        # also detect implicit (e.g., 7x) by looking for digits followed by variable
        for v in ("x","y","z","a","b","c"):
            if _re.search(rf"\d\s*{v}\b", t):
                vars.add(v)
    if not vars or len(vars) > 3:
        return None

    syms={v: sp.Symbol(v) for v in vars}
    trans = standard_transformations + (implicit_multiplication_application, convert_xor)

    def pe(expr: str):
        return parse_expr(expr, local_dict=syms, transformations=trans, evaluate=True)

    equations=[]
    for L,R in eqs:
        try:
            l=pe(L)
            r=pe(R)
        except Exception:
            return None
        equations.append(sp.Eq(l,r))

    ordered=[syms[v] for v in sorted(vars)]

    # enforce linearity + small size
    try:
        for eq in equations:
            e = (eq.lhs - eq.rhs)
            poly = sp.Poly(e, *ordered)
            if poly.total_degree() > 1:
                return None
            if poly.total_degree() < 0:
                return None
    except Exception:
        return None

    # solve
    try:
        solset = sp.linsolve(equations, ordered)
        sols = list(solset) if solset else []
    except Exception:
        sols=[]
    if not sols:
        try:
            sols2 = sp.solve(equations, ordered, dict=True)
            if sols2:
                sols=[tuple(d.get(sym) for sym in ordered) for d in sols2]
        except Exception:
            return None
    if not sols:
        return None

    tup=sols[0]
    if tup is None:
        return None
    assign={ordered[i]: tup[i] for i in range(len(ordered))}

    # requested expression (x+y / x-y / x+y+z)
    m = _re.search(r"\breturn\s+([xyzabc](?:\s*[\+\-]\s*[xyzabc]){1,4})\b", t, _re.I)
    if m:
        expr_str = m.group(1).replace(" ", "")
        try:
            expr = pe(expr_str)
            val = sp.nsimplify(expr.subs(assign))
            if val.is_integer:
                return str(int(val))
        except Exception:
            pass

    # common: x+y appears even without "return"
    if ("x" in vars) and ("y" in vars) and _re.search(r"\bx\s*\+\s*y\b", t):
        try:
            val = sp.nsimplify((syms["x"]+syms["y"]).subs(assign))
            if val.is_integer:
                return str(int(val))
        except Exception:
            pass

    # single variable query
    m2 = _re.search(r"\b(?:find|solve\s+for)\s+([xyzabc])\b", t, _re.I)
    if m2:
        v=m2.group(1)
        if v in vars:
            try:
                val = sp.nsimplify(assign[syms[v]])
                if val.is_integer:
                    return str(int(val))
            except Exception:
                pass

    return None

def _mpv7_solve(text: str):
    if not text:
        return None
    t=text.strip()
    if not t:
        return None
    if len(t) > 20000:
        return None

    m=_mpv7_re_fact_digitsum.search(t)
    if m:
        n=int(m.group(1))
        r=_mpv7_fact_digitsum(n)
        if r is not None:
            return r

    r=_mpv7_try_sympy_linear_system(t)
    if r is not None:
        return r

    return None

try:
    _MPV7_SOLVE0 = Solver.solve
    def _mpv7_solve_wrap(self, text):
        ans=_mpv7_solve(text)
        if ans is not None:
            return ans
        return _MPV7_SOLVE0(self, text)
    Solver.solve=_mpv7_solve_wrap
except Exception:
    pass
# === MPV7_PATCH_END ===
'''
    return src + patch

def main():
    with open(PATH,"r",encoding="utf-8") as f:
        src=f.read()
    out=_append_patch(src)
    with open(PATH,"w",encoding="utf-8",newline="\n") as f:
        f.write(out)
    print("PATCHED_MPV7")

if __name__=="__main__":
    main()
