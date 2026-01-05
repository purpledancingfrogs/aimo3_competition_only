import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from pathlib import Path

MODEL_PATH = Path(r"C:\Users\aureon\aimo_models\Qwen2.5-Math-7B-Instruct")

class DeterministicLLM:
    def __init__(self):
        torch.manual_seed(0)
        torch.use_deterministic_algorithms(True)

        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_PATH,
            trust_remote_code=True,
            local_files_only=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            local_files_only=True
        )
        self.model.eval()

    def solve(self, prompt: str, max_tokens: int = 256) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                do_sample=False,
                temperature=0.0,
                top_p=1.0,
                max_new_tokens=max_tokens
            )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

if __name__ == "__main__":
    llm = DeterministicLLM()
    print(llm.solve("Solve: 2*x + 3 = 11. Return final integer only."))
