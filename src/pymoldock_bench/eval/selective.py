from __future__ import annotations
from collections.abc import Iterable

def coverage(confidence_labels: Iterable[str]) -> float:
    labels=list(confidence_labels); return sum(x not in {"uncertain", ""} for x in labels)/len(labels) if labels else 0.0

def selective_accuracy(predicted: Iterable[str], truth: Iterable[str]) -> float:
    pairs=[(p,t) for p,t in zip(predicted,truth) if p not in {"uncertain", ""}]
    return sum(p==t for p,t in pairs)/len(pairs) if pairs else 0.0
