import json
from multiprocessing import Pool, cpu_count
from orchestrator import run

PROBLEMS = [
    "x+2=5",
    "2*x=10",
    "3*x-9=0"
]

def worker(problem):
    return run(problem)

if __name__ == "__main__":
    with Pool(min(50, cpu_count())) as p:
        results = p.map(worker, PROBLEMS)
    print(json.dumps(results, indent=2))
