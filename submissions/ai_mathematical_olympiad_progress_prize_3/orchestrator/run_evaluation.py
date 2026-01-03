import argparse
import csv
import json

from submissions.ai_mathematical_olympiad_progress_prize_3.orchestrator.load_solvers import load_solvers

def normalize(x):
    if x is None:
        return {}
    if isinstance(x, dict):
        return x
    return {"answer": x}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--time-budget", type=float, default=None)
    args = parser.parse_args()

    solver_container = load_solvers()
    if isinstance(solver_container, dict):
        solver = next(iter(solver_container.values()))[0]
    elif isinstance(solver_container, list):
        solver = solver_container[0]
    else:
        solver = solver_container

    results = []

    with open(args.input, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            problem = row[0]
            raw = solver.solve(problem)
            results.append(normalize(raw))

    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
