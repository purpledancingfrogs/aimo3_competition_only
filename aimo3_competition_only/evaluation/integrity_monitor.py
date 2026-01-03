# evaluation/integrity_monitor.py
# Deterministic execution watchdog (audit-safe, no wall-clock dependence)

MAX_STEPS_PRIMARY = 5_000_000
MAX_STEPS_FALLBACK = 1_000_000

class IntegrityMonitor:
    def __init__(self):
        self.steps = 0
        self.best_guess = None

    def step(self, n=1):
        self.steps += n
        if self.steps > MAX_STEPS_PRIMARY:
            raise RuntimeError("PRIMARY_LIMIT_EXCEEDED")

    def checkpoint(self, value):
        # value must be JSON-serializable
        self.best_guess = value

    def fallback_allowed(self):
        return self.steps <= (MAX_STEPS_PRIMARY + MAX_STEPS_FALLBACK)

    def reset(self):
        self.steps = 0
        self.best_guess = None
