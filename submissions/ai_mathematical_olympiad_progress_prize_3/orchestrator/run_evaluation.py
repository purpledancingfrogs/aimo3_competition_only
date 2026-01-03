import csv, json
from submissions.ai_mathematical_olympiad_progress_prize_3.orchestrator.load_solvers import load_solvers

def normalize_answer(x):
    return 0 if x is None else x

def main(input_path, report_path):
    solvers = load_solvers()
    nt_solver = solvers["NT"][0]  # FORCE deterministic NT routing

    results = []
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            problem = row.get("problem", "")
            pred = nt_solver.solve(problem)
            results.append({
                "id": row.get("id"),
                "problem": problem,
                "prediction": normalize_answer(pred)
            })

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    import sys
    main(sys.argv[sys.argv.index("--input")+1], sys.argv[sys.argv.index("--report")+1])
