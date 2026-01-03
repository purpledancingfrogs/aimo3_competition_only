import argparse
import json
import csv
from submissions.ai_mathematical_olympiad_progress_prize_3.orchestrator.load_solvers import load_solvers
from submissions.ai_mathematical_olympiad_progress_prize_3.orchestrator.run_evaluation import normalize

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    solvers = load_solvers()
    solver = list(solvers.values())[0][0]

    results = []

    with open(args.input, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            q = row.get("question") or row.get("problem") or row.get("input") or ""
            out = solver.solve(q)
            results.append({
                "id": row.get("id"),
                "prediction": out
            })

    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(normalize(results), f, indent=2)

if __name__ == "__main__":
    main()
