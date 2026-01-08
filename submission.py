import os
import time
import traceback

# --- CONFIG ---
KAGGLE_AGENT_PATH = "/kaggle/input/deepseek-math"  # placeholder; must exist on Kaggle if used
LOCAL_MODE = (os.name == "nt")
TIME_LIMIT_SEC = 9 * 60 * 60 - 300  # 9h minus 5m
START_TIME = time.time()

# --- OPTIONAL NEURAL AGENT (stub; safe to keep disabled) ---
class NeuralAgent:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        if not LOCAL_MODE:
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch
                # NOTE: Only works if KAGGLE_AGENT_PATH exists in Kaggle dataset inputs.
                self.tokenizer = AutoTokenizer.from_pretrained(KAGGLE_AGENT_PATH)
                self.model = AutoModelForCausalLM.from_pretrained(
                    KAGGLE_AGENT_PATH,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True,
                )
            except Exception:
                self.model = None
                self.tokenizer = None

    def generate_python_plan(self, problem: str):
        return None

# --- SYMBOLIC KERNEL ---
import solver  # must be pure; no side effects

def execute_with_safety(problem: str) -> int:
    # time budget gate
    if (time.time() - START_TIME) > TIME_LIMIT_SEC:
        return 0

    # neural path disabled by default (safe)
    # plan = neural_agent.generate_python_plan(problem)
    # if plan: ...

    # symbolic fallback
    try:
        # prefer official solve() if present; else allow solve_problem()
        if hasattr(solver, "solve"):
            out = solver.solve(problem)
        elif hasattr(solver, "solve_problem"):
            out = solver.solve_problem(problem)
        else:
            return 0

        # enforce integer-only
        try:
            return int(str(out).strip())
        except Exception:
            return int(float(str(out).strip()))
    except Exception:
        return 0

def mock_main():
    tests = [
        "2+2",
        "Solve 2*x=10",
        "gcd(100, 20)",
        "Minimize (x-5)^2",
    ]
    for p in tests:
        a = execute_with_safety(p)
        print(f"{p} -> {a}")

def main():
    # Kaggle environment (AIMO)
    try:
        import aimo
        env = aimo.make_env()
        iter_test = env.iter_test()
    except Exception:
        # local mode fallback
        return mock_main()

    neural_agent = NeuralAgent()  # kept for future, safe if load fails

    for test_df, sample_submission in iter_test:
        try:
            problem = str(test_df.iloc[0]["problem"])
            ans = execute_with_safety(problem)
            sample_submission["answer"] = int(ans)
            env.predict(sample_submission)
        except Exception:
            # never crash loop
            try:
                sample_submission["answer"] = 0
                env.predict(sample_submission)
            except Exception:
                pass

if __name__ == "__main__":
    main()