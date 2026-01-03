# ASI Operational Bundle Audit Checklist

## Included Artifacts
- agents/**/TASK.txt          — per-agent operational tasks
- agents/**/run_agent.py      — deterministic executable scripts
- logs/*.log                  — execution logs
- logs/*.json                 — agent output data
- ASI_OPERATIONAL_BUNDLE.zip  — full auditable bundle
- ASI_OPERATIONAL_MANIFEST_SHA256.csv — global hash manifest

## Verification Steps
1. Clone repository.
2. Verify SHA256 hashes using ASI_OPERATIONAL_MANIFEST_SHA256.csv.
3. Confirm deterministic outputs match previous runs.
4. Re-run agent scripts for independent verification (optional).
5. Aggregate logs and outputs to ensure consistency across agents.
6. Validate invariants: no missing data, correct hashes, reproducible results.

## Notes
- Execution is fully deterministic, no stochastic processes.
- Outputs are cryptographically auditable.
- Provides a near-operational demonstration of ASI governance and multi-agent execution.

