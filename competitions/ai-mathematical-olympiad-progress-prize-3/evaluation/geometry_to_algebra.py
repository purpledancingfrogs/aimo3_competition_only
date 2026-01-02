from evaluation.geometry.inversion_engine import InversionEngine

def try_inversion(constraints):
    eng = InversionEngine()
    eqs = []
    for c in constraints:
        if c["type"] == "tangent_circles":
            O = c["center"]
            R2 = c["R2"]
            for P in c["points"]:
                eqs.append(eng.invert_point(O, P, R2))
    return eqs
