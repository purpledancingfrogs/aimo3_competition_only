REPRODUCIBILITY PROOF

This solver is fully deterministic.

Verification procedure:
1) Run the solver twice on the same input set.
2) Capture stdout hashes and internal audit logs.
3) Assert bit-for-bit identity.

Determinism guarantees:
- No randomness
- Fixed solver order
- Fixed bound escalation
- Hard timeouts
- Canonical answer normalization

Any divergence constitutes a failure.
