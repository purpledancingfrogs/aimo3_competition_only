# Decision Structure Invariants

This module identifies decision-structure invariants that persist across domains, scales, and contexts.

An invariant is a structural property of a decision that remains true regardless of:
- domain (security, infrastructure, governance, AI, medicine)
- actor intent
- data completeness
- time pressure
- narrative framing

This repository extends `decision-decomposition` by moving from **components** to **laws**.

The goal is not optimization.
The goal is **predictive stability under uncertainty**.

## Contents

- `invariants.md` — formally stated decision invariants
- `mapping.md` — mapping invariants to real-world cases
- `cases/` — raw case descriptions
- `outputs/` — invariant extraction results

## Method Constraints

- No persuasion
- No moral framing
- No policy advocacy
- No outcome optimization
- Structural analysis only

If a decision violates an invariant, failure modes are guaranteed, not probabilistic.
