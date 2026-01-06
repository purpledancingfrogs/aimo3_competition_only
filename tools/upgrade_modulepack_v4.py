# tools/upgrade_modulepack_v4.py
# Bounded sympy-based equation/system handler + stronger normalization + safe injection into Solver.solve
from __future__ import annotations
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOLVER = ROOT / "solver.py"

def _find_solve_block(lines):
    # find "class Solver" then first "def solve("
    cls_i = None
    for i,ln in enumerate(lines):
        if re.match(r"^\s*class\s+Solver\b", ln):
            cls_i = i
            break
    if cls_i is None:
        return None
    for j in range(cls_i+1, len(lines)):
        if re.match(r"^\s*def\s+solve\s*\(", lines[j]):
            return j
    return None

def _inject_into_solve(lines, solve_i):
    indent = re.match(r"^(\s*)def\s+solve\s*\(", lines[solve_i]).group(1) + "    "
    # move past optional docstring if present
    k = solve_i + 1
    while k < len(lines) and lines[k].strip() == "":
        k += 1
    if k < len(lines) and re.match(r'^\s*("""|''') , lines[k]):
        q = lines[k].lstrip()[:3]
        k += 1
        while k < len(lines) and q not in lines[k]:
            k += 1
        if k < len(lines):
            k += 1
    inject = [
        f"{indent}# MODULEPACK_V4_INJECT\n",
        f"{indent}try:\n",
        f"{indent}    _r = _mpv4_try(prompt)\n",
        f"{indent}    if _r is not None:\n",
        f"{indent}        return _r\n",
        f"{indent}except Exception:\n",
        f"{indent}    pass\n",
        "\n"
    ]
    return lines[:k] + inject + lines[k:]

def patch():
    txt = SOLVER.read_text(encoding="utf-8")
    if "MODULEPACK_V4" in txt:
        print("ALREADY_PATCHED")
        return 0
    lines = txt.splitlines(True)

    solve_i = _find_solve_block(lines)
    if solve_i is None:
        print("ERROR: could not locate Solver.solve()")
        return 2

    # helper code inserted near top (after imports) to avoid forward refs
    helper = r'''
# =========================
# MODULEPACK_V4 (bounded)
# =========================
import math as _mpv4_math
import re as _mpv4_re

def _mpv4_norm(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    s = s.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
    s = s.replace("\u00d7", "*").replace("\u22c5", "*").replace("\u00f7", "/")
    s = s.replace("\u2261", "≡")
    s = s.replace("\u00b2", "^2").replace("\u00b3", "^3")
    s = s.replace("\u2074", "^4").replace("\u2075", "^5").replace("\u2076", "^6").replace("\u2077", "^7").replace("\u2078", "^8").replace("\u2079", "^9")
    s = s.replace("\u00a0", " ")
    s = _mpv4_re.sub(r"[ \t]+", " ", s)
    return s.strip()

def _mpv4_int(x):
    try:
        if isinstance(x, bool):
            return None
        if isinstance(x, int):
            return int(x)
        if hasattr(x, "is_integer") and x.is_integer():
            return int(x)
        if hasattr(x, "is_Integer") and bool(x.is_Integer):
            return int(x)
    except Exception:
        return None
    return None

def _mpv4_pick_expr(prompt: str):
    p = prompt.lower()
    if "x+y" in p or "x + y" in p: return ("x","y","+")
    if "x-y" in p or "x - y" in p: return ("x","y","-")
    if "x*y" in p or "x * y" in p or "xy" in p: return ("x","y","*")
    if "return x" in p and "return x+" not in p and "return x-" not in p: return ("x",None,None)
    if "return y" in p: return ("y",None,None)
    if "value of x" in p: return ("x",None,None)
    if "value of y" in p: return ("y",None,None)
    return None

def _mpv4_try_sympy(prompt: str):
    # bounded sympy: only for small systems/equations explicitly present
    try:
        import sympy as sp
    except Exception:
        return None
    s0 = _mpv4_norm(prompt)
    s = s0
    s = s.replace("^", "**")
    # quick handlers first (powmod/mod)
    m = _mpv4_re.search(r"compute\s+(\d+)\s*\*\*\s*(\d+)\s+mod\s+(\d+)", s.lower())
    if m:
        a=int(m.group(1)); b=int(m.group(2)); md=int(m.group(3))
        return str(pow(a,b,md))
    m = _mpv4_re.search(r"(\d+)\s*mod\s*(\d+)", s.lower())
    if m and "pow" not in s.lower() and "**" not in s:
        a=int(m.group(1)); md=int(m.group(2))
        return str(a % md)

    # factorial digit sum
    m = _mpv4_re.search(r"sum of digits of\s+(\d+)\s*!", s.lower())
    if m:
        n=int(m.group(1))
        if 0 <= n <= 3000:
            f=_mpv4_math.factorial(n)
            return str(sum(int(ch) for ch in str(f)))

    # gcd/lcm
    m = _mpv4_re.search(r"gcd\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", s.lower())
    if m:
        a=int(m.group(1)); b=int(m.group(2))
        return str(_mpv4_math.gcd(a,b))
    m = _mpv4_re.search(r"lcm\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", s.lower())
    if m:
        a=int(m.group(1)); b=int(m.group(2))
        g=_mpv4_math.gcd(a,b)
        return str(abs(a//g*b) if g else 0)

    # binomial
    m = _mpv4_re.search(r"(?:c|choose)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", s.lower())
    if m:
        n=int(m.group(1)); k=int(m.group(2))
        if 0 <= k <= n <= 20000 and k <= 2000:
            return str(_mpv4_math.comb(n,k))

    # CRT two congruences: x ≡ a (mod m) and x ≡ b (mod n)
    if "≡" in s0 and "mod" in s.lower():
        mm = _mpv4_re.findall(r"≡\s*(-?\d+)\s*\(mod\s*(\d+)\)", s0)
        if len(mm) >= 2:
            a1,m1 = int(mm[0][0]), int(mm[0][1])
            a2,m2 = int(mm[1][0]), int(mm[1][1])
            def egcd(a,b):
                if b==0: return (a,1,0)
                g,x,y=egcd(b,a%b)
                return (g,y,x-(a//b)*y)
            g,x,y = egcd(m1,m2)
            if (a2-a1) % g == 0:
                l = m1//g*m2
                k = ((a2-a1)//g * x) % (m2//g)
                sol = (a1 + k*m1) % l
                if "smallest" in s.lower() or "nonnegative" in s.lower():
                    return str(sol)
                return str(sol)

    # Extract equation lines with '='
    eq_lines = []
    for ln in s0.splitlines():
        if "=" in ln and any(ch.isalpha() for ch in ln):
            eq_lines.append(ln.strip())
    if not eq_lines and "=" in s0 and any(ch.isalpha() for ch in s0):
        # single-line prompt
        if s0.count("=") <= 3:
            eq_lines = [x.strip() for x in s0.split("\n") if "=" in x]

    if not eq_lines:
        return None

    # build symbols set (limit)
    sym_names = sorted(set(_mpv4_re.findall(r"\b[a-zA-Z]\b", " ".join(eq_lines))))
    sym_names = [x for x in sym_names if x.lower() not in ("e", "i")]
    if not sym_names:
        sym_names = ["x"]
    if len(sym_names) > 3:
        sym_names = sym_names[:3]
    syms = {name: sp.Symbol(name, integer=True) for name in sym_names}

    eqs = []
    for ln in eq_lines[:6]:
        parts = ln.split("=")
        if len(parts) != 2:
            continue
        L,R = parts
        try:
            Ls = sp.sympify(L.replace("^","**"), locals=syms)
            Rs = sp.sympify(R.replace("^","**"), locals=syms)
            eqs.append(sp.Eq(Ls, Rs))
        except Exception:
            continue

    if not eqs:
        return None

    vars_ = [syms[n] for n in sym_names]

    # solve system/equation; bounded
    try:
        sol = sp.solve(eqs, vars_, dict=True)
    except Exception:
        return None
    if not sol:
        return None
    sol = sol[0]
    # require all vars in solution to be integer-like
    vals = {}
    for v in vars_:
        if v not in sol:
            continue
        iv = _mpv4_int(sol[v])
        if iv is None:
            # allow rational exact integers
            try:
                if sol[v].is_Rational and sol[v].q == 1:
                    iv = int(sol[v])
                else:
                    return None
            except Exception:
                return None
        vals[str(v)] = int(iv)

    if not vals:
        return None

    pick = _mpv4_pick_expr(prompt)
    if pick:
        a,b,op = pick
        if b is None:
            if a in vals:
                return str(vals[a])
            return None
        if a in vals and b in vals:
            if op == "+": return str(vals[a] + vals[b])
            if op == "-": return str(vals[a] - vals[b])
            if op == "*": return str(vals[a] * vals[b])
    # default: single variable x if available
    if "x" in vals:
        return str(vals["x"])
    # else first value
    return str(next(iter(vals.values())))

def _mpv4_try(prompt: str):
    # returns string integer or None
    out = _mpv4_try_sympy(prompt)
    if out is None:
        return None
    out = str(out).strip()
    if not out:
        return None
    # enforce plain int string
    if _mpv4_re.fullmatch(r"[-+]?\d+", out):
        return out
    return None
# =========================
# END MODULEPACK_V4
# =========================
'''
    # place helper after initial imports block (best-effort)
    insert_at = 0
    for i,ln in enumerate(lines[:200]):
        if ln.startswith("class ") or re.match(r"^\s*class\s+", ln):
            insert_at = i
            break
    # ensure helper inserted before class Solver
    lines = lines[:insert_at] + [helper] + lines[insert_at:]

    # recompute solve index after insertion
    solve_i = _find_solve_block(lines)
    if solve_i is None:
        print("ERROR: solve not found after insertion")
        return 3
    lines = _inject_into_solve(lines, solve_i)

    SOLVER.write_text("".join(lines), encoding="utf-8")
    print("PATCHED")
    return 0

if __name__ == "__main__":
    raise SystemExit(patch())
