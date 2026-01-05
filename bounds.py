import time

I64_MIN = -(2**63)
I64_MAX = (2**63) - 1

class Guard:
    def __init__(self, max_steps=20000, max_seconds=1.8, max_abs=10**18):
        self.max_steps = int(max_steps)
        self.max_seconds = float(max_seconds)
        self.max_abs = int(max_abs)
        self._t0 = time.perf_counter()
        self._steps = 0

    def step(self, n=1):
        self._steps += int(n)
        if self._steps > self.max_steps:
            raise RuntimeError("BOUNDS:STEP_CAP")

    def time_ok(self):
        if (time.perf_counter() - self._t0) > self.max_seconds:
            raise RuntimeError("BOUNDS:TIME_CAP")

    def guard_int(self, x):
        if not isinstance(x, int):
            raise RuntimeError("BOUNDS:NON_INT")
        if x < I64_MIN or x > I64_MAX:
            raise RuntimeError("BOUNDS:I64_OVERFLOW")
        if x < -self.max_abs or x > self.max_abs:
            raise RuntimeError("BOUNDS:ABS_CAP")
        return x

def run_guarded(fn, fallback=0):
    g = Guard()
    try:
        g.time_ok()
        out = fn(g)
        return g.guard_int(int(out))
    except Exception:
        return int(fallback)
