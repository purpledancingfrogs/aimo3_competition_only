AIMO-3 Deterministic Solver Audit Artifacts (aimo3-compliance)

Core claims auditors must verify:
- Offline, deterministic, bounded execution
- Formal engines dominate (Z3/SymPy) where available
- Universal Modulo Guards (UMG) enforce residues on {2,3,5,7,11}
- Bounded Brute Verification (BBV) checks uniqueness in a fixed window
- Final answer normalized mod 1000 into [0,999]
