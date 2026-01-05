Determinism
- No randomness (no random, numpy RNG, sampling, time-based branching)
- Fixed escalation schedules
- Hard timeouts on solvers (process killer)
- Identical outputs across repeated runs on same inputs

PowerShell note:
- Do not use '<' redirection. Use: Get-Content file | python .\solver.py
