# AUREON DETERMINISTIC AGENT RUNNER (NORMALIZED OUTPUT FIXED)

import os
from solver import solve

def main():
    results = solve()
    if not results:
        raise RuntimeError("SOLVER_RETURNED_NO_RESULTS")

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    norm = os.path.join(root, 'normalized')
    os.makedirs(norm, exist_ok=True)

    out = os.path.join(norm, f"{agentName}.run.norm.txt")

    with open(out, 'w', encoding='utf-8') as f:
        for i, a in results:
            f.write(f"{i},{int(a)}\n")

if __name__ == "__main__":
    main()
