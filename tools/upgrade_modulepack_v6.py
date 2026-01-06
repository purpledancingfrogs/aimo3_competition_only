import re, math

PATH="solver.py"

def _append_patch(src: str) -> str:
    if "MPV6_PATCH_BEGIN" in src:
        print("ALREADY_PATCHED_MPV6")
        return src

    patch = r'''

# === MPV6_PATCH_BEGIN ===
import re as _re
import math as _math

# robust factorial digit-sum (handles punctuation after "!")
_mpv6_re_fact_digitsum = _re.compile(r"(?:sum\s+of\s+digits\s+of)\s+(\d{1,6})\s*!\s*[\.\,\)\]\s]*", _re.I)

def _mpv6_fact_digitsum(n: int):
    # bounded: avoid huge factorials in adversarial selfplay
    if n < 0 or n > 8000:
        return None
    f = _math.factorial(n)
    return str(sum((ord(c)-48) for c in str(f)))

# robust multi-equation extraction (works when equations are on one line)
_mpv6_eq_find = _re.compile(r"([0-9a-zA-Z+\-*/().\s]{1,120})=([0-9a-zA-Z+\-*/().\s]{1,120})")

def _mpv6_norm(s: str) -> str:
    # normalize common math glyphs
    s = s.replace("×","*").replace("−","-").replace("^","**")
    return s

def _mpv6_try_sympy_system(text: str):
    try:
        import sympy as sp
    except Exception:
        return None

    t = _mpv6_norm(text)

    eqs=[]
    for m in _mpv6_eq_find.finditer(t):
        L = m.group(1).strip()
        R = m.group(2).strip()
        # prune noise
        if not L or not R:
            continue
        if len(L) > 120 or len(R) > 120:
            continue
        # allow only safe chars
        if not _re.fullmatch(r"[0-9a-zA-Z+\-*/().\s]+", L):
            continue
        if not _re.fullmatch(r"[0-9a-zA-Z+\-*/().\s]+", R):
            continue
        eqs.append((L,R))
    if not eqs:
        return None
    if len(eqs) > 6:
        eqs = eqs[:6]

    # detect variables (prefer x,y,z,a,b,c)
    vars=set()
    for L,R in eqs:
        for v in ("x","y","z","a","b","c"):
            if _re.search(rf"\b{v}\b", L) or _re.search(rf"\b{v}\b", R):
                vars.add(v)
    if not vars or len(vars) > 3:
        return None

    syms = {v: sp.Symbol(v, integer=True) for v in vars}
    equations=[]
    for L,R in eqs:
        try:
            l = sp.sympify(L, locals=syms)
            r = sp.sympify(R, locals=syms)
            equations.append(sp.Eq(l,r))
        except Exception:
            return None

    ordered = [syms[v] for v in sorted(vars)]
    sol = None
    try:
        solset = sp.linsolve(equations, ordered)
        if solset:
            sol = list(solset)
    except Exception:
        sol = None
    if not sol:
        try:
            sol2 = sp.solve(equations, ordered, dict=True)
            if sol2:
                sol = [tuple(d.get(sym) for sym in ordered) for d in sol2]
        except Exception:
            return None
    if not sol:
        return None

    tup = sol[0]
    if tup is None:
        return None

    assign = {ordered[i]: tup[i] for i in range(len(ordered))}

    # request: x+y / x+y+z etc.
    m = _re.search(r"\breturn\s+([xyzabc](?:\s*[\+\-]\s*[xyzabc]){1,4})\b", t, _re.I)
    if m:
        expr_str = m.group(1).replace(" ", "")
        try:
            expr = sp.sympify(expr_str, locals=syms)
            val = sp.nsimplify(expr.subs(assign))
            if val.is_integer:
                return str(int(val))
        except Exception:
            pass

    # common: "return x+y"
    if ("x" in vars) and ("y" in vars) and _re.search(r"\bx\s*\+\s*y\b", t):
        try:
            val = sp.nsimplify((syms["x"]+syms["y"]).subs(assign))
            if val.is_integer:
                return str(int(val))
        except Exception:
            pass

    # otherwise single variable asked
    m2 = _re.search(r"\b(?:find|solve\s+for)\s+([xyzabc])\b", t, _re.I)
    if m2:
        v = m2.group(1)
        if v in vars:
            try:
                val = sp.nsimplify(assign[syms[v]])
                if val.is_integer:
                    return str(int(val))
            except Exception:
                pass

    return None

def _mpv6_solve(text: str):
    if not text:
        return None
    t = text.strip()
    if not t:
        return None
    if len(t) > 20000:
        return None

    # factorial digit sum (punctuation-tolerant)
    m = _mpv6_re_fact_digitsum.search(t)
    if m:
        n = int(m.group(1))
        r = _mpv6_fact_digitsum(n)
        if r is not None:
            return r

    # robust linear/system solver
    r = _mpv6_try_sympy_system(t)
    if r is not None:
        return r

    return None

# wrap current Solver.solve (may already have MPV4/MPV5 wrappers)
try:
    _MPV6_SOLVE0 = Solver.solve
    def _mpv6_solve_wrap(self, text):
        ans = _mpv6_solve(text)
        if ans is not None:
            return ans
        return _MPV6_SOLVE0(self, text)
    Solver.solve = _mpv6_solve_wrap
except Exception:
    pass
# === MPV6_PATCH_END ===
'''
    return src + patch

def main():
    with open(PATH, "r", encoding="utf-8") as f:
        src = f.read()
    out = _append_patch(src)
    with open(PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    print("PATCHED_MPV6")

if __name__ == "__main__":
    main()
