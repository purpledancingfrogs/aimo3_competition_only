import re
from fractions import Fraction

_SAFE_EVAL_GLOBALS = {"__builtins__": None}

class NTSolver:
    def __init__(self):
        pass

    def _normalize(self, text: str) -> str:
        if not text:
            return ""
        # strip LaTeX wrappers + dollar math
        text = re.sub(r'\\\(|\\\)|\\\[|\\\]|\$', '', text)

        # normalize common LaTeX ops / unicode minus
        text = text.replace('\\times', '*').replace('\\cdot', '*')
        text = text.replace('\u2212', '-')  # unicode minus

        # drop common instruction scaffolding
        text = re.sub(r'\bSolve\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bWhat\s+is\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bfor\s*x\b\.?', '', text, flags=re.IGNORECASE)

        # remove punctuation we don't need, collapse whitespace
        text = text.replace('?', '').replace('.', '')
        text = "".join(text.split())

        return text

    def _safe_eval_num(self, s: str):
        return eval(s, _SAFE_EVAL_GLOBALS, {})

    def _parse_linear_lhs(self, lhs: str):
        # returns (a,b) for lhs = a*x + b
        # supports: 4+x, x+4, 2x-3, -x+2, 3*x+5, 4+2*x, etc.
        if not lhs:
            return None

        # normalize implicit multiplication: "2x" -> "2*x"
        lhs = re.sub(r'(\d)(x)\b', r'\1*\2', lhs, flags=re.IGNORECASE)

        # split into signed terms: convert "-" into "+-" then split by "+"
        s = lhs.replace('-', '+-')
        parts = [p for p in s.split('+') if p != ""]

        a = Fraction(0)
        b = Fraction(0)

        for term in parts:
            term = term.strip()
            if term == "":
                continue

            if 'x' in term.lower():
                t = term.lower().replace('x', '')
                t = t.replace('*', '')
                if t in ("", "+"):
                    coef = Fraction(1)
                elif t == "-":
                    coef = Fraction(-1)
                else:
                    coef = Fraction(self._safe_eval_num(t))
                a += coef
            else:
                b += Fraction(self._safe_eval_num(term))

        return (a, b)

    def _solve_linear(self, expr: str):
        try:
            if '=' not in expr:
                # plain arithmetic
                if 'x' in expr.lower():
                    return None
                v = self._safe_eval_num(expr)
                if isinstance(v, bool):
                    return int(v)
                return int(v) if int(v) == v else v

            lhs, rhs = expr.split('=', 1)
            lhs = lhs.strip()
            rhs = rhs.strip()

            # normalize implicit multiplication in rhs too (rare)
            rhs = re.sub(r'(\d)(x)\b', r'\1*\2', rhs, flags=re.IGNORECASE)

            if 'x' in rhs.lower():
                return None  # keep it simple/deterministic: only solve for x on LHS

            parsed = self._parse_linear_lhs(lhs)
            if not parsed:
                return None
            a, b = parsed
            if a == 0:
                return None

            rhs_val = Fraction(self._safe_eval_num(rhs))
            x = (rhs_val - b) / a

            if x.denominator == 1:
                return int(x.numerator)
            return f"{x.numerator}/{x.denominator}"
        except Exception:
            return None

    def solve(self, problem_text):
        # guard: sometimes callers accidentally pass file paths
        if isinstance(problem_text, str) and (problem_text.endswith(".csv") or problem_text.endswith(".parquet")):
            return 0

        t = self._normalize(problem_text)
        out = self._solve_linear(t)
        return out if out is not None else 0
