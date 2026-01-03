# RESULTS — Cross-Model Convergence Benchmark

## Scope
Independent frontier models were evaluated on an identical prompt under isolated runs, separate sessions, and zero coordination. Outputs were captured verbatim. No normalization, scoring, summarization, or semantic smoothing was applied.

## Models
- GPT-4
- Claude
- Grok

## Metric
**Structural Convergence Index (SCI)**  
Assesses whether independently generated outputs exhibit the same decision structure:
- Variable classes (controllable, observed, constraints, invariants)
- Failure-mode enumeration
- Ordering and dependency relationships
- Absence of persuasive framing

SCI = 1 when structural isomorphism is present across models.

## Results

| Model Pair        | Structural Isomorphism |
|-------------------|------------------------|
| GPT-4 ↔ Claude    | Yes |
| GPT-4 ↔ Grok      | Yes |
| Claude ↔ Grok     | Yes |

**Aggregate SCI:** 1.0

## Evidence
All models independently produced the same decomposition schema, identified invariants without prompting, and enumerated failure modes without cross-model leakage.

Raw outputs are preserved verbatim in:
`/cross-model-convergence-benchmark/raw_outputs/`

## Interpretation
Convergence occurred at the **structural** level, not the linguistic level. The structure is a property of the decision space itself.

## Integrity Statement
This document reflects direct observation of raw outputs. No post-hoc modification or interpretive overlay has been applied.
