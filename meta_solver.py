from router import route

def solve(problem):
    try:
        return route(problem)
    except Exception:
        return ""
