import math
import re

# Deterministic fractal-dimension handlers for common olympiad-style prompts.
# Outputs an integer when the problem asks for an integer result; otherwise returns None.

def _log_ratio(n: int, d: int) -> float:
    return math.log(n) / math.log(d)

def try_fractal_dimension(text: str):
    s = text.strip().lower()

    # Known canonical self-similar sets (exact dimension is log(a)/log(b))
    # If the problem later asks for an integer derived from this, solver.py will handle it downstream.
    known = {
        "koch": (4, 3),
        "sierpinski triangle": (3, 2),
        "sierpiński triangle": (3, 2),
        "sierpinski gasket": (3, 2),
        "sierpiński gasket": (3, 2),
        "sierpinski carpet": (8, 3),
        "sierpiński carpet": (8, 3),
        "menger sponge": (20, 3),
        "cantor set": (2, 3),
        "middle-third cantor": (2, 3),
        "middle third cantor": (2, 3),
    }
    for k,(a,b) in known.items():
        if k in s:
            return ("dimension", a, b)

    # Generic rule: "each step replaces with N copies scaled by factor 1/M"
    # Example: "replace each segment by 5 segments each 1/4 as long" -> dim = log 5 / log 4
    m = re.search(r"(?:replace|replaces|replaced).{0,80}?\b(\d+)\b.{0,40}?\b(?:copies|segments|parts)\b.{0,80}?\b(?:scale|scaled|scaling)\b.{0,40}?\b(?:1\s*/\s*(\d+)|1\/(\d+))", s)
    if m:
        n = int(m.group(1))
        d = int(m.group(2) or m.group(3))
        if n > 0 and d > 1:
            return ("dimension", n, d)

    # Digit-restriction Cantor-type sets: "base b, allow m digits"
    # Example: "base 5, digits {0,2,4}" -> m=3, b=5 -> dim=log 3/log 5
    m = re.search(r"\bbase\s+(\d+)\b", s)
    if m:
        b = int(m.group(1))
        # count explicit digits in a set {...}
        m2 = re.search(r"\{([^}]+)\}", s)
        if m2:
            digits = re.findall(r"-?\d+", m2.group(1))
            if digits:
                m_allowed = len(set(digits))
                if m_allowed > 0 and b > 1:
                    return ("dimension", m_allowed, b)

    return None

def dimension_value(a: int, b: int) -> float:
    return _log_ratio(a, b)
