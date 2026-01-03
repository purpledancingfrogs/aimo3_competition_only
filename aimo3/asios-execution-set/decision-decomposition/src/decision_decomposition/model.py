from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Variable:
    name: str
    kind: str  # "controllable" | "observed"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Constraint:
    expression: str

@dataclass
class Invariant:
    expression: str

@dataclass
class FailureMode:
    description: str
    trigger: str

@dataclass
class DecisionModel:
    variables: List[Variable]
    constraints: List[Constraint]
    invariants: List[Invariant]
    failure_modes: List[FailureMode]
