"""
Entanglement Tracker

Tracks coupled signal states under observation.
Entanglement increases contradiction pressure.
"""

class EntanglementTracker:
    def __init__(self, coupling: float = 0.25):
        self.coupling = coupling

    def entangle(self, states: dict):
        keys = list(states.keys())
        entangled = states.copy()

        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                a, b = keys[i], keys[j]
                delta = self.coupling * min(states[a], states[b])
                entangled[a] += delta
                entangled[b] += delta

        # renormalize
        total = sum(entangled.values())
        for k in entangled:
            entangled[k] /= total if total != 0 else 1.0

        return entangled
