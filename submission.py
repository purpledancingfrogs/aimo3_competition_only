import os
import sys
import time
import subprocess
import traceback
import re
import pandas as pd

# --- CONFIGURATION & INVARIANTS ---
KAGGLE_AGENT_PATH = "/kaggle/input/deepseek-math"
LOCAL_MODE = os.name == 'nt'
TIME_LIMIT_SEC = 9 * 60 * 60 - 300
START_TIME = time.time()

# --- UTILITY: CODE EXECUTION ---
def run_generated_code(code, timeout=5):
    try:
        wrapped_code = "import sys\nimport math\nfrom sympy import *\n" + code
        result = subprocess.run(
            [sys.executable, "-c", wrapped_code],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            return lines[-1].strip() if lines else None
        return None
    except Exception:
        return None

# --- AGENT ALPHA: THE NEURAL ARCHITECT ---
class NeuralAgent:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        if not LOCAL_MODE:
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch
                self.tokenizer = AutoTokenizer.from_pretrained(KAGGLE_AGENT_PATH)
                self.model = AutoModelForCausalLM.from_pretrained(
                    KAGGLE_AGENT_PATH,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True
                )
            except Exception:
                self.model = None
                self.tokenizer = None

    def generate_python_plan(self, problem):
        if not self.model:
            return None
        prompt = f"""User: {problem}
Please write a Python script to solve this problem.
The script should print the final answer as a single integer modulo 1000.
Use 'sympy' or brute force loops if necessary.
Wrap the code in ```python ... ``` blocks.
Assistant:
"""
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.0,
                do_sample=False
            )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            code_match = re.search(r"```python(.*?)```", response, re.DOTALL)
            return code_match.group(1) if code_match else None
        except Exception:
            return None

# --- AGENT BETA: THE SYMBOLIC EXECUTOR ---
import solver

def execute_with_safety(problem):
    if (time.time() - START_TIME) > TIME_LIMIT_SEC:
        return 0

    agent = NeuralAgent()
    plan = agent.generate_python_plan(problem)
    if plan:
        ans = run_generated_code(plan)
        if ans is not None:
            try:
                return int(float(ans))
            except Exception:
                pass

    try:
        return solver.solve_problem(problem)
    except Exception:
        return 0

def main():
    try:
        import aimo
        env = aimo.make_env()
        iter_test = env.iter_test()
    except ImportError:
        return

    for test_df, sample_submission in iter_test:
        try:
            problem = str(test_df.iloc[0].get('problem', ''))
            answer = execute_with_safety(problem)
            try:
                final_answer = int(float(str(answer))) % 1000
            except Exception:
                final_answer = 0
            sample_submission['answer'] = final_answer
            env.predict(sample_submission)
        except Exception:
            sample_submission['answer'] = 0
            env.predict(sample_submission)

if __name__ == "__main__":
    main()