"""Paradox Simulator
Maintains contradiction instead of resolving it.
"""

def contradiction_index(states):
    return 1.0 - max(states.values())
