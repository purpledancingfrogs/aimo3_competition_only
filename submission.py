import os
import sys
import time
import subprocess
import traceback
import re
import pandas as pd

# --- CONFIGURATION ---
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
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            return lines[-1].strip() if lines else None
    except:
        pass
    return None

# --- AGENT ALPHA: NEURAL ARCHITECT ---
class NeuralAgent:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        if not LOCAL_MODE:
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch
                print("[NEURAL] Loading DeepSeek-Math...")
                self.tokenizer = AutoTokenizer.from_pretrained(KAGGLE_AGENT_PATH)
                self.model = AutoModelForCausalLM.from_pretrained(
                    KAGGLE_AGENT_PATH,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True
                )
            except Exception as e:
                print(f"[NEURAL] Load Failed: {e}")

    def generate_python_plan(self, problem):
        if not self.model:
            return None
        prompt = f"User: {problem}\nWrite a Python script to solve this. Print the final integer answer.\nAssistant:\n"
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(**inputs, max_new_tokens=512, do_sample=False)
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            match = re.search(r"```python(.*?)```", response, re.DOTALL)
            return match.group(1) if match else None
        except:
            return None

# --- AGENT BETA: THE LADDER ANCHOR ---
import solver

def execute_with_safety(problem):
    # 1. TIME CHECK
    if (time.time() - START_TIME) > TIME_LIMIT_SEC:
        return 0

    # 2. FAST PATH: THE LADDER (Zero Entropy)
    try:
        fast_ans = solver.solve(problem)
        if fast_ans != "0":
            return fast_ans
    except:
        pass

    # 3. SLOW PATH: THE NEURAL CORTEX (High Energy)
    agent = NeuralAgent()
    plan = agent.generate_python_plan(problem)
    if plan:
        ans = run_generated_code(plan)
        if ans:
            try:
                return int(float(ans))
            except:
                pass

    # 4. FALLBACK: ZERO RETURN
    return 0

# --- MAIN LOOP ---
def main():
    try:
        import aimo
        env = aimo.make_env()
        iter_test = env.iter_test()
    except ImportError:
        return mock_main()

    for test_df, sample_submission in iter_test:
        try:
            problem = str(test_df.iloc[0]['problem'])
            answer = execute_with_safety(problem)
            sample_submission['answer'] = int(float(str(answer)))
            env.predict(sample_submission)
        except:
            sample_submission['answer'] = 0
            env.predict(sample_submission)

def mock_main():
    print("[MOCK] Testing Ladder-First Integration...")
    tests = ["2+2", "Solve 2x+10=20", "gcd(50, 20)"]
    for p in tests:
        print(f"'{p}' -> {execute_with_safety(p)}")

if __name__ == "__main__":
    main()