import re, pathlib

p = pathlib.Path("solver.py")
src = p.read_text(encoding="utf-8")

marker = "### AUREON_GENERAL_SOLVER_PATCH_V1 ###"
if marker not in src:
    raise SystemExit("NO_PATCH_MARKER_FOUND")

# Replace wrapper to only fallback on (a) exception/empty, or (b) original==0 but prompt implies nonzero/positive.
pat = re.compile(r"def _AUREON__solve_wrapper\(self, text\):.*?\nif _AUREON__Solver is not None:", re.DOTALL)
m = pat.search(src)
if not m:
    raise SystemExit("WRAPPER_BLOCK_NOT_FOUND")

new_wrapper = r'''
def _AUREON__solve_wrapper(self, text):
    # preserve original behavior first
    out_s = ""
    if _AUREON__orig_solve is not None:
        try:
            out = _AUREON__orig_solve(self, text)
            out_s = str(out).strip() if out is not None else ""
            if out_s != "":
                # If original says 0, only treat as failure when prompt *implies* nonzero/positive.
                if out_s == "0":
                    t = _norm_text(text).lower()
                    nonzero_hint = any(k in t for k in [
                        "positive integer", "positive", "greater than 0", "nonzero", "not equal to 0", "natural number"
                    ])
                    if not nonzero_hint:
                        return out_s
                else:
                    return out_s
        except Exception:
            out_s = ""
    try:
        g = solve_general(text)
        # If original returned 0 and general returns nonzero, prefer general.
        if out_s == "0" and str(g).strip() not in ("", "0"):
            return str(g).strip()
        return str(g).strip() if str(g).strip() != "" else (out_s if out_s != "" else "0")
    except Exception:
        return out_s if out_s != "" else "0"

if _AUREON__Solver is not None:
'''
src2 = src[:m.start()] + new_wrapper + src[m.end():]

p.write_text(src2, encoding="utf-8")
print("PATCH_WRAPPER_V2_OK")
