import argparse
import csv
import json

from submissions.ai_mathematical_olympiad_progress_prize_3.orchestrator.load_solvers import load_solvers

def normalize(x):
    if x is None:
        return None
    if isinstance(x, dict):
        return x
    return x

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()

    solver_container = load_solvers()
    if isinstance(solver_container, dict):
        solver = next(iter(solver_container.values()))[0]
    elif isinstance(solver_container, list):
        solver = solver_container[0]
    else:
        solver = solver_container

    results = []

    with open(args.input, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Kaggle AIMO-3 CSV uses a 'problem' column
            problem = row.get('problem') or row.get('question') or ''
            raw = solver.solve(problem)
            results.append({
                'id': row.get('id'),
                'problem': problem,
                'prediction': normalize(raw)
            })

    with open(args.report, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

if __name__ == '__main__':
    main()
