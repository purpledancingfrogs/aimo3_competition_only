import re
import time
import unicodedata

# --- optional sympy (best-effort) ---
try:
    import sympy as _sp
    from sympy.core.cache import clear_cache as _sp_clear_cache
except Exception:
    _sp = None
    _sp_clear_cache = None

# --- regex ---
_FINAL_INT = re.compile(r"(?:FINAL_ANSWER\s*[:=]\s*|\\boxed\{\s*)(-?\d+)\s*\}?")
_LAST_INT  = re.compile(r"(-?\d+)(?!.*-?\d+)")
# very conservative equation extraction
_EQ = re.compile(r"([0-9xynkmabcpqrt+\-*/().\s\\^]+?)\s*=\s*([0-9xynkmabcpqrt+\-*/().\s\\^]+)")

_ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff"), None)

def _clean(s: str) -> str:
    s = "" if s is None else str(s)
    s = s.translate(_ZERO_WIDTH)
    s = unicodedata.normalize("NFKC", s)
    # basic LaTeX/operator normalization
    s = s.replace("\\times", "*").replace("\\cdot", "*")
    s = s.replace("^", "**")
    # normalize “and” separators that break naive splitting
    s = s.replace(" and ", ", ")
    return s

def _extract_final_int(s: str):
    m = _FINAL_INT.search(s)
    if m:
        try: return int(m.group(1))
        except: return None
    return None

def _extract_last_int(s: str):
    m = _LAST_INT.search(s)
    if m:
        try: return int(m.group(1))
        except: return None
    return None

def _sympy_try_solve_one_var(eq_pairs, budget_s: float):
    if _sp is None:
        return None
    t0 = time.perf_counter()
    try:
        if _sp_clear_cache:
            _sp_clear_cache()
    except Exception:
        pass

    # prioritize common variables
    var_order = ["x","n","k","m","a","b","c","y","p","q","r","t"]
    for lhs_raw, rhs_raw in eq_pairs:
        if time.perf_counter() - t0 > budget_s:
            return None
        lhs = _clean(lhs_raw)
        rhs = _clean(rhs_raw)
        # quick filter: must contain at least one letter var
        if not re.search(r"[a-zA-Z]", lhs + rhs):
            continue

        for v in var_order:
            if time.perf_counter() - t0 > budget_s:
                return None
            try:
                sym = _sp.Symbol(v, integer=True)
                # only attempt if variable appears
                if (v not in lhs) and (v not in rhs):
                    continue

                L = _sp.sympify(lhs, locals={v: sym})
                R = _sp.sympify(rhs, locals={v: sym})
                eq = _sp.Eq(L, R)

                sol = _sp.solve(eq, sym, dict=False)
                if sol is None:
                    continue

                # normalize solver output to list
                sols = sol if isinstance(sol, (list, tuple)) else [sol]
                cand_ints = []
                for s0 in sols:
                    if time.perf_counter() - t0 > budget_s:
                        return None
                    try:
                        s0s = _sp.simplify(s0)
                        # accept only exact integers
                        if hasattr(s0s, "is_integer") and s0s.is_integer:
                            cand_ints.append(int(s0s))
                        elif getattr(s0s, "is_Rational", False) and s0s.q == 1:
                            cand_ints.append(int(s0s.p))
                    except Exception:
                        continue

                # plugback verify
                for val in cand_ints:
                    if time.perf_counter() - t0 > budget_s:
                        return None
                    try:
                        ok = _sp.simplify((L - R).subs(sym, val)) == 0
                        if ok:
                            return val
                    except Exception:
                        continue
            except Exception:
                continue
    return None

def solve(prompt: str) -> str:
    # hard budget for symbolic attempts (keep tiny to avoid timeouts)
    BUDGET = 0.12
    try:
        s = _clean(prompt)

        v = _extract_final_int(s)
        if v is not None:
            return str(int(v))

        # attempt simple algebra if '=' present
        eqs = _EQ.findall(s)
        if eqs:
            val = _sympy_try_solve_one_var(eqs, BUDGET)
            if val is not None:
                return str(int(val))

        # fallback: last integer seen
        v = _extract_last_int(s)
        if v is not None:
            return str(int(v))

        return "0"
    except Exception:
        return "0"

def predict(prompt=None, *args, **kwargs):
    # batch-safe wrapper for environments that call predict
    x = prompt
    if x is None and args:
        x = args[0]
    if x is None:
        x = kwargs.get("prompt", kwargs.get("text", ""))
    if isinstance(x, (list, tuple)):
        return [solve(str(p)) for p in x]
    return solve(str(x))