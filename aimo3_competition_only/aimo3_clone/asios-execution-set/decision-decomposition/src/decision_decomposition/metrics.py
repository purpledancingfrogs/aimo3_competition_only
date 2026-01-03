def summarize(metrics: dict) -> dict:
    return {
        "time_to_clarity_seconds": metrics["time_to_clarity_seconds"],
        "coverage": {
            "variables": metrics["variable_count"],
            "constraints": metrics["constraint_count"],
            "failure_modes": metrics["failure_mode_count"],
        },
    }
