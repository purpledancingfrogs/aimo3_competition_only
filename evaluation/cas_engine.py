# evaluation/cas_engine.py
# Minimal deterministic symbolic core (extensible)

from fractions import Fraction

class MultivariatePolynomial:
    def __init__(self, terms=None):
        self.terms = terms or {}  # {(exp_tuple): Fraction}

    def __add__(self, other):
        out = dict(self.terms)
        for k,v in other.terms.items():
            out[k] = out.get(k, Fraction(0)) + v
            if out[k] == 0:
                del out[k]
        return MultivariatePolynomial(out)

    def __mul__(self, other):
        out = {}
        for (e1,c1) in self.terms.items():
            for (e2,c2) in other.terms.items():
                e = tuple(a+b for a,b in zip(e1,e2))
                out[e] = out.get(e, Fraction(0)) + c1*c2
        return MultivariatePolynomial(out)
