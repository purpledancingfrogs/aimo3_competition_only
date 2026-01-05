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

import math
import re

def _pow_int(a: int, n: int) -> int:
    if n < 0: return 0
    out = 1
    for _ in range(n):
        out *= a
    return out

def try_fractal_counts(text: str):
    s = (text or "").strip().lower()
    # normalize unicode
    s = s.replace("–","-").replace("—","-")

    # Find iteration count
    it = None
    m = re.search(r"\bafter\s+(\d+)\s+(?:iterations|steps|stages)\b", s)
    if m: it = int(m.group(1))
    m = re.search(r"\bin\s+the\s+(\d+)(?:st|nd|rd|th)\s+(?:iteration|step|stage)\b", s)
    if m: it = int(m.group(1))
    if it is None:
        m = re.search(r"\b(\d+)\s+(?:iterations|steps|stages)\b", s)
        if m: it = int(m.group(1))

    # Replacement factor: each segment -> k segments
    k = None
    m = re.search(r"\beach\s+(?:step|iteration|stage)\s+(?:replaces|replace)\s+each\s+(?:segment|side|edge|line)\s+with\s+(\d+)\s+(?:segments|sides|edges|parts)\b", s)
    if m: k = int(m.group(1))
    m = re.search(r"\breplace\s+each\s+(?:segment|side|edge|line)\s+by\s+(\d+)\s+(?:segments|sides|edges|parts)\b", s)
    if m: k = int(m.group(1))

    # Initial count
    init = None
    if "triangle" in s: init = 3
    if "square" in s: init = 4
    if "cube" in s: init = 12  # edges
    if "segment" in s and init is None: init = 1

    # Known fractals (count of pieces each iteration)
    # Return integers only when question is explicitly counting objects.
    wants_count = any(w in s for w in ["how many", "number of", "count", "total", "segments", "sides", "edges", "pieces", "small squares", "small cubes", "triangles"])

    if not wants_count:
        return None

    # Koch snowflake (triangle start, each side -> 4 segments)
    if "koch" in s and it is not None:
        kk = 4 if k is None else k
        init2 = 3 if init is None else init
        return init2 * _pow_int(kk, it)

    # Sierpinski triangle: number of small triangles = 3^n (if counting triangles)
    if ("sierpinski" in s or "sierpiński" in s) and "triangle" in s and it is not None:
        return _pow_int(3, it)

    # Sierpinski carpet: number of remaining small squares = 8^n
    if ("sierpinski" in s or "sierpiński" in s) and "carpet" in s and it is not None:
        return _pow_int(8, it)

    # Menger sponge: number of remaining cubes = 20^n
    if "menger" in s and "sponge" in s and it is not None:
        return _pow_int(20, it)

    # Generic replacement count
    if it is not None and k is not None and init is not None:
        return init * _pow_int(k, it)

    return None
