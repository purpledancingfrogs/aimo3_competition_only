# ARC-AGI Swarm Audit Checklist

## Artifacts
- agents/**/ARC_TASKS/puzzles.json      — generated ARC puzzles
- agents/**/ARC_TASKS/solutions.json    — deterministic solutions
- agents/**/ARC_TASKS/verification.json — solution verification outputs
- ARC_AGI_BUNDLE.zip                    — aggregated bundle
- ARC_AGI_MANIFEST_SHA256.csv           — global integrity hashes

## Verification Steps
1. Clone repository.
2. Verify SHA256 hashes using ARC_AGI_MANIFEST_SHA256.csv.
3. Normalize outputs and check solution convergence across agents.
4. Confirm deterministic puzzle generation and solution correctness.
5. Optional: re-run missions to confirm reproducibility.

