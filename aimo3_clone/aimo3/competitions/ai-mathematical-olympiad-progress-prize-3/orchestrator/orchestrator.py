# AIMO-3 Orchestrator
# Routes problems, enforces budgets, aggregates answers

import time
from collections import Counter

DOMAINS = ["NT", "ALG", "GEO", "COMB"]

def route_problem(text):
    if any(k in text.lower() for k in ["prime", "mod", "divis"]):
        return "NT"
    if any(k in text.lower() for k in ["triangle", "circle", "angle"]):
        return "GEO"
    if any(k in text.lower() for k in ["graph", "count", "ways"]):
        return "COMB"
    return "ALG"

def orchestrate(problem_id, text, solvers, time_budget=90):
    domain = route_problem(text)
    answers = []
    start = time.time()
    for solver in solvers.get(domain, []):
        if time.time() - start > time_budget:
            break
        ans = solver.solve(text)
        if ans is not None:
            answers.append(ans)
    if not answers:
        return None, 0.0
    vote = Counter(answers).most_common(1)[0]
    confidence = vote[1] / len(answers)
    return vote[0], confidence
