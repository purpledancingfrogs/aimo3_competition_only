# AIMO-3 Submission Auditor Instructions (Repo-Local)

## A) Freeze invariants (must all match)
Run:
- git rev-parse HEAD
- git rev-parse aimo3-submission-ready
- git rev-parse aimo3-kaggle-submit

Require:
- HEAD == tag(aimo3-submission-ready) == branch(aimo3-kaggle-submit)

## B) Audit bundle integrity
Files:
- audit/AIMO3_AUDIT_RECORD.txt
- audit/AIMO3_Competition_Final_Audit_Bundle.zip

Require:
- record "hash=" equals SHA256 of the zip
- zip is tracked by git (git ls-files audit/AIMO3_Competition_Final_Audit_Bundle.zip)

## C) Kaggle contract
Entrypoint and gateway must exist in repo root:
- kaggle_evaluation/aimo_3_inference_server.py
- kaggle_evaluation/aimo_3_gateway.py

Gateway contract:
- AIMO3Gateway.predict(data_batch: polars.DataFrame) -> polars.DataFrame
- returns DataFrame with a single column: answer (int)

## D) Determinism / security
No network calls; no randomness; no subprocess; no external model calls.

## E) Quick smoke tests (must pass)
Run tools\self_audit.ps1 (prints refs/hashes + runs 1+1 through solver and gateway).
