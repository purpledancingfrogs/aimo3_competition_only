# AIMO3 DSS-O Solver Core

This dataset contains the **DSS-O (Deterministic Symbolic Solver – Omega)** core used by **Aureon** for the AI Mathematical Olympiad – Progress Prize 3 (AIMO-3).

## Purpose
Provide a clean, minimal, competition-safe solver core that can be imported directly into a Kaggle Notebook and used to generate `submission.parquet` deterministically.

This dataset is not training data.
It contains only executable solver logic and verification utilities, fully compliant with Kaggle rules.

## Included Files
- solver_core.py — main symbolic solving engine
- router.py — problem-type dispatcher
- solver_modules.zip — arithmetic, algebra, geometry, logic modules
- verifier.py — output sanity and determinism checks
- reference.csv — local reference for offline validation
- README.md — this document

## Kaggle Usage Pattern
from meta_solver import solve

Kaggle automatically provides the `test` dataframe.
The notebook must iterate rows and emit:

id, answer

into `submission.parquet`.

## Determinism
- No randomness
- No internet
- No model calls
- Pure symbolic and rule-based execution

## Status
Actively maintained during competition iteration toward 50/50 correctness.

Last updated: 2026-01-03
