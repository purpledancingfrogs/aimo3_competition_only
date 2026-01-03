import math

def entropy(distribution: dict) -> float:
    return -sum(
        p * math.log2(p)
        for p in distribution.values()
        if p > 0
    )
