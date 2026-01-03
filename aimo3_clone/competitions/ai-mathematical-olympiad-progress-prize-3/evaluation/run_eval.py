# Evaluation runner (no submission)

from orchestrator.orchestrator import orchestrate
from orchestrator.load_solvers import load_solvers

def evaluate(problems):
    solvers = load_solvers()
    results = []
    for pid, text in problems:
        ans, conf = orchestrate(pid, text, solvers)
        results.append({'id': pid, 'answer': ans, 'confidence': conf})
    return results
