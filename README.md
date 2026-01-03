# AIMO-3 Deterministic Solver (DSS-Ω)

This solver is fully deterministic and audit-safe.

## Properties
- No randomness
- No learning
- No external calls
- Rule-based dispatch only

## Supported Problem Classes
- Arithmetic: sum, product, gcd, lcm, difference, ratio
- Modular arithmetic
- Integer exponentiation
- Linear equations in one variable (x)

## Design
parser → canonicalizer → deterministic dispatcher → arithmetic modules

This design is intended to be fully inspectable and reproducible.
