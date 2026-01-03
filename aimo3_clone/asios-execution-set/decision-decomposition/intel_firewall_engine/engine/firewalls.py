from dataclasses import dataclass, field
from typing import Dict
import time

@dataclass
class Firewall:
    name: str
    opacity: float  # 0–1, higher = stronger destruction
    created_at: float = field(default_factory=time.time)

    def transmit(self, signal: Dict[str, float]) -> Dict[str, float]:
        return {k: v * (1 - self.opacity) for k, v in signal.items()}
