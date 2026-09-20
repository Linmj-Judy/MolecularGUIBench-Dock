from __future__ import annotations
from collections.abc import Iterable

def interaction_f1(predicted: Iterable[str], truth: Iterable[str]) -> float:
    p, t = set(predicted), set(truth); tp = len(p & t)
    precision = tp / len(p) if p else 0.0; recall = tp / len(t) if t else (1.0 if not p else 0.0)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0
