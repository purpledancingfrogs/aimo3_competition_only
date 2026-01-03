from __future__ import annotations
import os
import sys
import pandas as pd

from solver_core import dss_omega_solver

def run_reference_eval(csv_path: str = "reference.csv") -> int:
    if not os.path.exists(csv_path):
        print(f"[verifier] missing {csv_path} (expected columns: problem, answer)")
        return 2

    df = pd.read_csv(csv_path)
    if "problem" not in df.columns or "answer" not in df.columns:
        print("[verifier] invalid CSV schema (need columns: problem, answer)")
        return 2

    correct = 0
    total = len(df)

    for _, r in df.iterrows():
        pred = dss_omega_solver(str(r["problem"]))
        try:
            gold = int(str(r["answer"]).strip())
            if int(pred) == gold:
                correct += 1
        except Exception:
            pass

    print(f"Reference score: {correct}/{total}")
    return 0

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "reference.csv"
    raise SystemExit(run_reference_eval(path))
