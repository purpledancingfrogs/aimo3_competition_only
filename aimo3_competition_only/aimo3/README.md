# Aureon Swarm Deterministic Convergence Proof

This repository contains a fully auditable, deterministic swarm execution run.

## What is Proven
- 50 independent agents executed parallel missions
- Outputs were normalized and compared
- Convergence measured via SHA256 hash identity
- All artifacts are reproducible and independently verifiable

## How to Verify (Any LLM / Human)
1. Clone this repo
2. Recompute SHA256 hashes of all files
3. Compare against PROOF_MANIFEST_SHA256.csv
4. Re-run normalization + convergence scripts if desired

## Key Artifacts
- /agents/**/TASK.txt            — agent-assigned tasks
- /logs/*.run.log                — raw execution logs
- /normalized/*.norm.txt          — normalized outputs
- convergence_matrix.csv          — pairwise hash comparison
- convergence_summary.txt         — convergence counts
- PROOF_MANIFEST_SHA256.csv       — global integrity ledger
- RESULTS_BUNDLE.zip              — frozen audit bundle

## Claim Boundary
This demonstrates deterministic multi-agent convergence,
not probabilistic sampling, hallucination, or prompt agreement.

Reproducibility > persuasion.
