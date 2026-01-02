AIMO-3 SWARM SOLVER

Root: C:\aureon-swarm
Agents: 50 (active)

This directory hosts the live solver architecture for
AI Mathematical Olympiad – Progress Prize 3.

Structure:
- architecture/  -> system design, guarantees, gates
- orchestrator/  -> routing, time budgets, voting
- agents/        -> domain-specialized solver agents
- evaluation/    -> confidence tracking, submit gate

Rule:
NO submission until =40 problems solved with consensus.
