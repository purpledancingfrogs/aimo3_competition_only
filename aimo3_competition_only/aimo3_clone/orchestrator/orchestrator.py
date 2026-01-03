import json, os
from invariants import extract
from solvers.linear import solve as solve_linear
from solvers.quadratic import solve as solve_quadratic
from solvers.number_theory import solve as solve_nt
from verifiers.linear import verify as verify_linear
from verifiers.quadratic import verify as verify_quadratic
from verifiers.number_theory import verify as verify_nt
from logger import log

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def route(problem: str, inv):
    if inv["degree"] == 1 and "y" not in problem:
        return "linear"
    if inv["degree"] == 2:
        return "quadratic"
    if "y" in problem:
        return "number_theory"
    raise ValueError("unsupported_problem")

def run(problem: str):
    inv = extract(problem)
    solver = route(problem, inv)

    if solver == "linear":
        ans = solve_linear(problem)
        ok = verify_linear(problem, ans)
    elif solver == "quadratic":
        ans = solve_quadratic(problem)
        ok = verify_quadratic(problem, ans)
    elif solver == "number_theory":
        ans = solve_nt(problem)
        ok = verify_nt(problem, ans)

    report = {
        "problem": problem,
        "invariants": inv,
        "solver": solver,
        "answer": ans,
        "verified": ok
    }
    return log(report)

if __name__ == "__main__":
    problems = ["x+2=5", "x^2-4=0", "2*x+3*y=7"]
    records = [run(p) for p in problems]
    with open(os.path.join(LOG_DIR, "run.json"), "w") as f:
        json.dump(records, f, indent=2)
    print(json.dumps(records, indent=2))
# Kaggle AIMO-3 compatibility entrypoint
def orchestrate(*args, **kwargs):
    if 'run' in globals() and callable(run):
        return run(*args, **kwargs)
    raise RuntimeError('No run() function found for orchestrate()')
