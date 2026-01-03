# intel-firewall-engine/engine/primitives.py

from dataclasses import dataclass, field
from typing import Dict, List, Any
import time


@dataclass
class EntangledVariable:
    """
    Represents variables whose states are interdependent.
    Observing one alters the joint state.
    """
    name: str
    states: Dict[str, float]  # state -> probability
    last_observed: float = field(default_factory=time.time)

    def observe(self, state: str):
        if state not in self.states:
            raise ValueError("Invalid state")
        # Collapse toward observed state
        for k in self.states:
            self.states[k] *= 0.1
        self.states[state] = 1.0
        self.normalize()
        self.last_observed = time.time()

    def normalize(self):
        total = sum(self.states.values())
        if total == 0:
            raise ValueError("Degenerate entangled state")
        for k in self.states:
            self.states[k] /= total


@dataclass
class Firewall:
    """
    Represents a transformation that destroys mutual information.
    """
    name: str
    loss_factor: float  # 0 < loss_factor <= 1

    def apply(self, signal: Dict[str, float]) -> Dict[str, float]:
        return {k: v * self.loss_factor for k, v in signal.items()}


@dataclass
class EvaporationPath:
    """
    Models gradual information loss over time.
    """
    half_life_seconds: float

    def decay(self, signal: Dict[str, float], elapsed: float) -> Dict[str, float]:
        decay_factor = 0.5 ** (elapsed / self.half_life_seconds)
        return {k: v * decay_factor for k, v in signal.items()}


@dataclass
class InvariantCheck:
    """
    Checks whether required structural invariants hold.
    """
    required_keys: List[str]

    def validate(self, signal: Dict[str, Any]) -> List[str]:
        violations = []
        for k in self.required_keys:
            if k not in signal or signal[k] is None:
                violations.append(k)
        return violations
