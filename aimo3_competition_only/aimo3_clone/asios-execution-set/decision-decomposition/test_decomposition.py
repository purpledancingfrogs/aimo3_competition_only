from decision_decomposition.decompose import decompose

def test_basic_decomposition():
    problem = {
        "knowns": {"demand": "high"},
        "unknowns": ["failure_location"],
        "constraints": ["hospital_power == continuous"],
    }
    result = decompose(problem)
    assert result["metrics"]["variable_count"] > 0
    assert result["metrics"]["constraint_count"] == 1
