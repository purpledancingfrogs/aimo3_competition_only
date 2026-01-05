import json, time
import importlib

def load():
    gw = importlib.import_module("kaggle_evaluation.aimo_3_gateway")
    srv = importlib.import_module("kaggle_evaluation.aimo_3_inference_server")
    sol = importlib.import_module("solver")
    return gw, srv, sol

def main():
    gw, srv, sol = load()
    print("IMPORT_OK")

    # Determine callable the server exposes (common patterns)
    candidates = []
    for name in ["predict", "Predictor", "solve", "run", "inference"]:
        if hasattr(srv, name):
            candidates.append(name)

    print("SERVER_ATTRS:", candidates)

    # Probe solver callables
    s_candidates = [n for n in ["solve","predict"] if hasattr(sol, n)]
    print("SOLVER_ATTRS:", s_candidates)

    # Minimal prompts of increasing messiness
    prompts = [
        "Problem 1 Problem: Alice and Bob are each holding some integer number of sweets. Answer: 50",
        "Compute: 2*x + 3 = 11. Return integer only.",
        "Let n ≥ 6 be a positive integer. We call ... (truncated).",
        "garbage input ####",
        ""
    ]

    # Try direct solver.solve first
    if hasattr(sol, "solve"):
        for i,p in enumerate(prompts,1):
            t0=time.time()
            try:
                y = sol.solve(p)
            except Exception as e:
                y = f"EXC:{type(e).__name__}:{e}"
            dt=int((time.time()-t0)*1000)
            print(f"SOLVE{i}={y} ms={dt}")

    # Try server.predict if exists and callable
    if hasattr(srv, "predict") and callable(getattr(srv,"predict")):
        for i,p in enumerate(prompts,1):
            t0=time.time()
            try:
                y = srv.predict(p)
            except Exception as e:
                y = f"EXC:{type(e).__name__}:{e}"
            dt=int((time.time()-t0)*1000)
            print(f"PRED{i}={y} ms={dt}")

if __name__ == "__main__":
    main()
