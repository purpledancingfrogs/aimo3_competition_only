from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

_WS = re.compile(r"\s+")
_INT = re.compile(r"[-+]?\d+")
_LATEX_INLINE = re.compile(r"\$(.+?)\$")
_LATEX_DISPLAY = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)

KEYWORDS = {
    "gcd": ("gcd", "greatest common divisor"),
    "lcm": ("lcm", "least common multiple"),
    "sum": ("sum", "total"),
    "product": ("product", "multiply", "times"),
    "difference": ("difference", "minus", "subtract"),
    "ratio": ("ratio", "quotient", "divide", "over"),
    "mod": ("mod", "modulo", "remainder"),
    "prime": ("prime", "primes"),
    "factor": ("factor", "factors"),
    "solve": ("solve", "find", "determine"),
    "equation": ("equation", "=", "equals"),
}

def _norm(s: str) -> str:
    s = s.replace("\u2212", "-")  # unicode minus
    s = s.replace("×", "*").replace("·", "*")
    s = s.replace("÷", "/")
    s = _WS.sub(" ", s).strip()
    return s

def _extract_latex(s: str) -> str:
    m = _LATEX_DISPLAY.search(s)
    if m:
        return m.group(1).strip()
    m = _LATEX_INLINE.search(s)
    if m:
        return m.group(1).strip()
    return ""

def _ints(s: str) -> List[int]:
    return [int(x) for x in _INT.findall(s)]

@dataclass(frozen=True)
class Parsed:
    raw: str
    text: str
    latex: str
    nums: List[int]
    flags: Dict[str, bool]

def parse_problem(problem: str) -> Parsed:
    raw = problem if problem is not None else ""
    text = _norm(str(raw)).lower()
    latex = _extract_latex(str(raw))

    nums = _ints(text)
    flags: Dict[str, bool] = {}
    for k, vocab in KEYWORDS.items():
        flags[f"has_{k}"] = any(v in text for v in vocab)

    # lightweight operator signals
    flags["has_plus"] = "+" in text or " plus " in f" {text} "
    flags["has_pow"] = "^" in text or "**" in text or " power " in f" {text} "
    flags["has_frac"] = "/" in text or " over " in f" {text} "

    return Parsed(raw=raw, text=text, latex=latex, nums=nums, flags=flags)
