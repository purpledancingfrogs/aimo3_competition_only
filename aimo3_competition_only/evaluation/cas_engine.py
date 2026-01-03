# evaluation/cas_engine.py
# Deterministic multivariate polynomial engine (pure Python, stdlib only)

from fractions import Fraction
from itertools import combinations

class MultivariatePolynomial:
    def __init__(self, terms=None):
        # terms: dict[tuple[int], Fraction]
        self.terms = terms or {}
        self._clean()

    def _clean(self):
        self.terms = {k: v for k, v in self.terms.items() if v != 0}

    def __add__(self, other):
        out = dict(self.terms)
        for k, v in other.terms.items():
            out[k] = out.get(k, Fraction(0)) + v
        return MultivariatePolynomial(out)

    def __sub__(self, other):
        out = dict(self.terms)
        for k, v in other.terms.items():
            out[k] = out.get(k, Fraction(0)) - v
        return MultivariatePolynomial(out)

    def __mul__(self, other):
        out = {}
        for e1, c1 in self.terms.items():
            for e2, c2 in other.terms.items():
                exp = tuple(a + b for a, b in zip(e1, e2))
                out[exp] = out.get(exp, Fraction(0)) + c1 * c2
        return MultivariatePolynomial(out)

    def leading_term(self):
        if not self.terms:
            return None, Fraction(0)
        exp = max(self.terms.keys())
        return exp, self.terms[exp]

    def monic(self):
        exp, coeff = self.leading_term()
        if coeff == 0:
            return self
        inv = Fraction(1, 1) / coeff
        return MultivariatePolynomial({e: c * inv for e, c in self.terms.items()})

    def degree(self):
        if not self.terms:
            return 0
        return max(sum(e) for e in self.terms)

    def reduce(self, basis):
        f = MultivariatePolynomial(dict(self.terms))
        changed = True
        while changed:
            changed = False
            for g in basis:
                lt_f, lc_f = f.leading_term()
                lt_g, lc_g = g.leading_term()
                if lt_f is None or lt_g is None:
                    continue
                if all(a >= b for a, b in zip(lt_f, lt_g)):
                    exp = tuple(a - b for a, b in zip(lt_f, lt_g))
                    factor = MultivariatePolynomial({exp: lc_f / lc_g})
                    f = f - factor * g
                    changed = True
                    break
        return f

def lcm_exp(e1, e2):
    return tuple(max(a, b) for a, b in zip(e1, e2))

def s_polynomial(f, g):
    lt_f, lc_f = f.leading_term()
    lt_g, lc_g = g.leading_term()
    lcm = lcm_exp(lt_f, lt_g)
    ef = tuple(a - b for a, b in zip(lcm, lt_f))
    eg = tuple(a - b for a, b in zip(lcm, lt_g))
    return (MultivariatePolynomial({ef: Fraction(1)}) * f -
            MultivariatePolynomial({eg: Fraction(1)}) * g)

def groebner_basis(polys):
    G = [p.monic() for p in polys]
    pairs = set(combinations(range(len(G)), 2))
    while pairs:
        i, j = pairs.pop()
        S = s_polynomial(G[i], G[j])
        R = S.reduce(G)
        if R.terms:
            R = R.monic()
            idx = len(G)
            G.append(R)
            for k in range(idx):
                pairs.add((k, idx))
    return G
