import time
from typing import Dict, Any, Iterable
from .model import Variable, Constraint, Invariant, FailureMode, DecisionModel

def _extract_keys(obj: Any) -> Iterable[str]:
    if isinstance(obj, dict):
        return obj.keys()
    if isinstance(obj, list):
        keys = []
        for item in obj:
            if isinstance(item, dict):
                keys.extend(item.keys())
        return keys
    return []

def decompose(problem: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()

    variables = []

    for k in _extract_keys(problem.get("knowns", {})):
        variables.append(Variable(name=k, kind="observed"))

    for k in problem.get("unknowns", []):
        variables.append(Variable(name=k, kind="observed"))

    for k in ["crew_allocation", "load_shedding_policy"]:
        variables.append(Variable(name=k, kind="controllable"))

    constraints = [
        Constraint(expression=c)
        for c in problem.get("constraints", [])
    ]

    invariants = [
        Invariant(expression="critical_services_priority > general_distribution"),
        Invariant(expression="frequency_violation increases cascading_risk"),
    ]

    failure_modes = [
        FailureMode(
            description="Delayed load shedding causes transformer damage",
            trigger="demand > capacity for extended duration",
        ),
        FailureMode(
            description="Generator fuel depletion at hospitals",
            trigger="fuel_resupply_delay",
        ),
    ]

    model = DecisionModel(
        variables=variables,
        constraints=constraints,
        invariants=invariants,
        failure_modes=failure_modes,
    )

    elapsed = round(time.time() - start, 6)

    return {
        "model": model,
        "metrics": {
            "time_to_clarity_seconds": elapsed,
            "variable_count": len(variables),
            "constraint_count": len(constraints),
            "failure_mode_count": len(failure_modes),
        },
    }