import re

def route(problem: str) -> str:
    p = problem.lower()

    # algebra first (avoid arithmetic swallowing equations)
    if "x" in p or "=" in p:
        return "algebra"

    # geometry next
    if any(k in p for k in ["triangle","circle","angle","square","radius","area","perimeter"]):
        return "geometry"

    # arithmetic last
    if re.search(r"[0-9][+\-*/]", p):
        return "arithmetic"

    return "unknown"
