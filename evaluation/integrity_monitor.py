# evaluation/integrity_monitor.py
# Deterministic Watchdog + Reproducibility Gate (NO time(), NO randomness)

class IntegrityMonitor:
    """
    Counts logical operations instead of wall-clock time.
    Enforces deterministic fallbacks.
    """

    def __init__(self, max_steps):
        self.max_steps = max_steps
        self.steps = 0
        self.tripped = False

    def tick(self, n=1):
        self.steps += n
        if self.steps > self.max_steps:
            self.tripped = True
            raise RuntimeError("STEP LIMIT EXCEEDED")

    def reset(self):
        self.steps = 0
        self.tripped = False


class DeterministicGate:
    """
    Stage controller:
    1. Exact symbolic
    2. Bounded discrete
    3. Deterministic fallback
    """

    def __init__(self, step_limit=5_000_000):
        self.monitor = IntegrityMonitor(step_limit)

    def run(self, stages):
        for stage in stages:
            try:
                self.monitor.reset()
                return stage(self.monitor)
            except RuntimeError:
                continue
        return None
