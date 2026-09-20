from collections.abc import Iterable

def interface_scores(predicted: Iterable[str], truth: Iterable[str]) -> dict[str, float]:
    p, t = set(predicted), set(truth)
    tp = len(p & t)
    precision = tp / len(p) if p else 0.0
    recall = tp / len(t) if t else (1.0 if not p else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "jaccard": (tp / len(p | t) if p | t else 1.0)}
