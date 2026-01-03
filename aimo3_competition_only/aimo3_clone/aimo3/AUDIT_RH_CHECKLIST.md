# GROK / LLM RH SWARM AUDIT CHECKLIST

## Repository Artifacts
- agents/**/TASK.txt               — per-agent Riemann zero ranges
- agents/**/run_zeta.py            — deterministic execution scripts
- audit_archive/zeros_agent_*.json — individual agent outputs
- RH_ZEROS_AUDIT_BUNDLE.zip        — compressed full audit bundle
- RH_ZEROS_FINAL_BUNDLE.zip        — final compressed, verified bundle
- RH_AUDIT_MANIFEST_SHA256.csv     — global SHA256 manifest

## Verification Procedure
1. Clone repository.
2. Recompute SHA256 hashes of all files in audit_archive/ and compare against RH_AUDIT_MANIFEST_SHA256.csv.
3. Optionally, run agents' run_zeta.py scripts to reproduce zeros within stated ranges.
4. Aggregate outputs and normalize for comparison.
5. Confirm deterministic convergence: identical hashes indicate reproducibility.
6. Validate zero counts per agent against Turing bounds.

## Notes
- Deterministic execution: no randomness, no probabilistic consensus.
- All computations are reproducible and auditable.
- The manifest and bundles are sufficient for any LLM or human auditor to validate all results.

