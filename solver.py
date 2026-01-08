import re

_FINAL_INT = re.compile(r"(?:FINAL_ANSWER\s*[:=]\s*|\\boxed\{\s*)(-?\d+)\s*\}?")
_LAST_INT  = re.compile(r"(-?\d+)(?!.*-?\d+)")

def _extract_prompt(prompt=None, *args, **kwargs):
    if prompt is None:
        if args:
            prompt = args[0]
        else:
            prompt = kwargs.get("prompt", kwargs.get("text", ""))
    if isinstance(prompt, dict):
        prompt = prompt.get("prompt", prompt.get("text", ""))
    return prompt

def _solve_one(text: str) -> str:
    try:
        s = "" if text is None else str(text)

        m = _FINAL_INT.search(s)
        if m:
            return str(int(m.group(1)))

        m = _LAST_INT.search(s)
        if m:
            return str(int(m.group(1)))

        return "0"
    except Exception:
        return "0"

def solve(prompt=None, *args, **kwargs) -> str:
    x = _extract_prompt(prompt, *args, **kwargs)
    return _solve_one(x)

def predict(prompt=None, *args, **kwargs):
    x = _extract_prompt(prompt, *args, **kwargs)
    if isinstance(x, (list, tuple)):
        return [_solve_one(p) for p in x]
    return _solve_one(x)