import sys, argparse, csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from orchestrator.orchestrator import orchestrate
from orchestrator.load_solvers import load_solvers

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--time-budget", type=int, default=90)
    args = ap.parse_args()

    solvers = load_solvers()
    results = []

    with open(args.input, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row["id"]
            text = row.get("problem", "") or row.get("text", "")
            ans, conf = orchestrate(pid, text, solvers, time_budget=args.time_budget)
            results.append({"id": pid, "answer": ans, "confidence": conf})

    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
