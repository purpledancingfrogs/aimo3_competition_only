import re

def heuristic_solve(p: str):
    p = p.strip()

    # Simple integer
    if re.fullmatch(r"-?\d+", p):
        return int(p)

    # a+b, a-b, a*b
    m = re.fullmatch(r"\s*(-?\d+)\s*([\+\-\*])\s*(-?\d+)\s*", p)
    if m:
        a, op, b = int(m[1]), m[2], int(m[3])
        if op == "+": return a + b
        if op == "-": return a - b
        if op == "*": return a * b

    return None
