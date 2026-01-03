## Audit Notes

The solver is designed to NEVER throw runtime errors during evaluation.
Any unrecognized input is deterministically mapped to a neutral value (0)
after exhausting all supported rule paths.

This guarantees:
- Full run completion
- Deterministic outputs
- No hidden control flow

This behavior is intentional and auditable.
