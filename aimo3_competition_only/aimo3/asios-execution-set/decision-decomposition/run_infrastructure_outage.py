import yaml
from decision_decomposition.decompose import decompose
from decision_decomposition.metrics import summarize

with open("examples/infrastructure_outage.yaml", "r") as f:
    problem = yaml.safe_load(f)

result = decompose(problem)
summary = summarize(result["metrics"])

print(summary)
