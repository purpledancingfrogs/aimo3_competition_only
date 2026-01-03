# ASIOS Execution Set

Canonical, auditable execution manifest for Aureon / ASIOS.

## Overview
This repository defines the authoritative **execution set**: a deterministic map of runnable executors, their entrypoints, and working directories.  
It is the bridge between governed intent and concrete execution.

## Structure
- execution_set.yaml — declarative executor registry
- siosctl.py — unified controller
- .github/workflows/ — CI validation
- Executors live in sibling folders:
  - decision-decomposition
  - QuantumMeasurementContradictionKit
  - ecursive-paradox-governance

## Usage

Run an executor:
`ash
python asiosctl.py run decision-decomposition
python asiosctl.py run qmck
git add README.md; git commit -m "Add top-level README documenting ASIOS execution set"; git push
Set-Content execution_set.yaml @"
version: 1
executors:
  decision-decomposition:
    description: Deterministic decision decomposition engine
    workdir: decision-decomposition
    entrypoint: run_infrastructure_outage.py
    type: python

  qmck:
    description: Quantum Measurement Contradiction Kit
    workdir: QuantumMeasurementContradictionKit/src
    entrypoint: -m qmck
    type: python

  recursive-paradox-governance:
    description: Recursive paradox governance adapters and ingestion
    workdir: recursive-paradox-governance
    entrypoint: cli.py
    type: python
