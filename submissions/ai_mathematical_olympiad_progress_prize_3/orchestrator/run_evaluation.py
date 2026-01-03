import argparse
import json
from sympy import Integer, Rational, Expr

def normalize(o):
    if isinstance(o, dict):
        return {k: normalize(v) for k, v in o.items()}
    if isinstance(o, list):
        return [normalize(v) for v in o]
    if isinstance(o, Integer):
        return int(o)
    if isinstance(o, Rational):
        return float(o)
    if isinstance(o, Expr):
        try:
            return int(o)
        except Exception:
            try:
                return float(o)
            except Exception:
                return str(o)
    return o

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--time-budget", type=float, default=None)
    args = parser.parse_args()

    from submissions.ai_mathematical_olympiad_progress_prize_3.orchestrator.load_solvers import load_solvers
    solvers = load_solvers(); solver = solvers['solver'] if 'solver' in solvers else list(solvers.values())[0]

    solver_container = solver
if isinstance(solver_container, dict):
    solver_obj = next(iter(solver_container.values()))[0]
elif isinstance(solver_container, list):
    solver_obj = solver_container[0]
else:
    solver_obj = solver_container
raw_results = solver_obj.solve(args.input)
    results = normalize(raw_results)

    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
