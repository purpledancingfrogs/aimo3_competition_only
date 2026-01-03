# Case 001 — Infrastructure Outage

## Context
A regional power grid experiences a cascading failure resulting in loss of service to hospitals, communications, and transportation.

## Decision Objective
Restore critical services while minimizing secondary harm.

## Variables
- Power generation capacity
- Grid topology
- Repair crew availability
- Weather conditions
- Demand prioritization

## Constraints
- Physical repair time
- Safety limits for crews
- Legal/regulatory requirements

## Invariants
- Human life preservation has priority
- Hospitals receive power before commercial users
- Repairs cannot exceed safety tolerances

## Failure Modes
- Premature grid restart
- Resource misallocation
- Communication breakdown
