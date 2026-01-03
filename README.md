# AIMO-3 Compliance Submission

## Structure
- solver.py  — deterministic symbolic solver (stdlib only)
- run.py     — single entrypoint (CSV → CSV)
- requirements.txt — intentionally empty (stdlib only)

## Usage
python run.py input.csv output.csv

## Guarantees
- Deterministic
- No randomness
- No filesystem side effects beyond specified output
- Standard library only
- Single solver, single entrypoint
