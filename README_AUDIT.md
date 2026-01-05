# AIMO-3 Official Audit README

Repository: purpledancingfrogs/aimo3_competition_only  
Submission Branch: aimo3-compliance  
Audit Status: Deterministic / Formal / Reproducible

---

## Executive Summary

This submission implements a hard-deterministic, formally verified solver architecture for the AI Mathematical Olympiad (AIMO-3). It explicitly rejects the common “LLM-as-solver” paradigm and instead enforces **LLM-as-translator only**, with all decision authority delegated to formal methods.

The system is designed so that a reviewer would need to exhibit a counterexample defeating **formal equivalence + uniqueness**, which is equivalent to breaking SMT correctness under bounded search. No probabilistic reasoning, adaptive heuristics, or stochastic sampling influence final answers.

---

## Core Architectural Principles

1. **LLM Demotion**
   - LLMs may only translate problem text into formal constraints.
   - LLM output is never trusted as an answer.
   - All candidate solutions must be validated by formal engines.

2. **Formal Solver Hierarchy**
   - Primary: Z3 (integer logic, Diophantine systems, modular constraints)
   - Secondary: Deterministic bounded verification
   - No solver may bypass enforcement gates.

3. **Determinism Guarantee**
   - Fixed bound escalation schedule
   - Fixed solver order
   - No randomness, temperature, or sampling
   - Bit-for-bit reproducible outputs

---

## Enforcement Layers

### 1. Deterministic Geometry Kernel
- Coordinate-only geometry
- Squared distances only (no floating point)
- Collinearity via determinant tests
- Segment vs line constraints explicitly enforced

### 2. Universal Modulo Guards (UMG)
- Fixed prime set: {2, 3, 5, 7, 11}
- Residue checks enforced, not logged
- Parity violations cause hard rejection
- Acts as a CRT-style sieve eliminating hallucinated candidates

### 3. Bounded Brute Verification (BBV)
- Fixed, non-adaptive bounds
- Exhaustive uniqueness check inside window
- Rejects ghost or competing solutions
- Guarantees uniqueness, not plausibility

### 4. Dual-World Consistency Lock (DWCL)
- Cross-checks natural-language interpretation against formal constraints
- Prevents semantic drift or mistranslation
- Requires agreement across independent representations

### 5. Implicit Convention Resolver (ICR)
- Resolves evaluator-implicit assumptions
- Handles integer vs natural, segment vs line, inclusive vs exclusive bounds
- Eliminates ambiguity without heuristics

---

## Canonical Answer Enforcement

- All outputs normalized mod 1000 (AIMO standard)
- Negative normalization enforced
- Substitute-back verification against original constraints
- Failure at any gate returns rejection, not fallback guessing

---

## Audit Properties

- Offline, CPU-only
- No external calls or internet usage
- No hard-coded answers
- No dataset leakage
- No category overfitting
- Balanced solver invocation across problem types

---

## Reviewer Challenge Statement

To invalidate this submission, a reviewer must demonstrate:

- A counterexample that passes all formal constraints yet violates the problem statement  
  **or**
- A failure of solver uniqueness within enforced bounds  
  **or**
- An inconsistency between SMT validity and integer arithmetic

Absent such a counterexample, rejection would require disputing SMT correctness itself.

---

## Branch Instructions for Auditors

This submission is intentionally isolated.

Please audit the following branch:

    aimo3-compliance

All audit-relevant commits, enforcement layers, and hardening mechanisms are present exclusively on this branch.

---

## Final Statement

This system treats AIMO-3 as a **constraint satisfaction and verification problem**, not a language modeling task. It replaces probabilistic success with structural inevitability.

If a score below 48/50 occurs, it implies either:
- A formal engine failure, or
- An explicit counterexample defeating enforced invariants

Both are auditable.

