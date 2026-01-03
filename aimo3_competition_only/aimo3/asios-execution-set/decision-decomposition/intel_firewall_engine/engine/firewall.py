"""
intel_firewall_engine.engine.firewall

Core intelligence firewall abstraction.
Preserves contradiction instead of resolving it.
"""

from typing import Dict


class IntelligenceFirewall:
    """
    Models an intelligence boundary that:
    - Accepts signals
    - Enforces observation costs
    - Preserves paradox instead of collapsing it
    """

    def __init__(self, name: str, permeability: float = 0.5):
        """
        :param name: Identifier for the firewall instance
        :param permeability: 0.0 = fully opaque, 1.0 = fully transparent
        """
        self.name = name
        self.permeability = max(0.0, min(1.0, permeability))
        self.history = []

    def observe(self, signal: Dict[str, float]) -> Dict[str, float]:
        """
        Observe an incoming signal.
        Observation reshapes the signal without resolving it.
        """
        observed = {}
        for k, v in signal.items():
            observed[k] = v * self.permeability

        self.history.append(
            {
                "input": signal,
                "output": observed,
            }
        )

        return observed

    def contradiction_index(self) -> float:
        """
        Measures how much information was suppressed vs passed through.
        """
        if not self.history:
            return 0.0

        total_in = 0.0
        total_out = 0.0

        for entry in self.history:
            total_in += sum(entry["input"].values())
            total_out += sum(entry["output"].values())

        if total_in == 0:
            return 0.0

        return 1.0 - (total_out / total_in)
