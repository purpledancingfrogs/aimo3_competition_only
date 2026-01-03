"""
Firewall Evaporation

Models information loss under sustained observation.
Contradiction is conserved, not eliminated.
"""

class FirewallEvaporation:
    def __init__(self, leakage_rate: float = 0.1):
        self.leakage_rate = leakage_rate

    def evaporate(self, states: dict):
        evaporated = {}
        total = sum(states.values())

        for k, v in states.items():
            loss = v * self.leakage_rate
            evaporated[k] = v - loss

        # renormalize
        norm = sum(evaporated.values())
        for k in evaporated:
            evaporated[k] /= norm if norm != 0 else 1.0

        return evaporated
