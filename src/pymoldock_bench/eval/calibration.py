from __future__ import annotations
import numpy as np

def expected_calibration_error(confidence, correct, bins: int = 10) -> float:
    c, y = np.asarray(confidence, float), np.asarray(correct, float)
    if c.shape != y.shape: raise ValueError("confidence and correct must have equal shape")
    if not len(c): return 0.0
    edges = np.linspace(0, 1, bins + 1); ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (c >= lo) & ((c < hi) | ((hi == 1) & (c <= hi)))
        if mask.any(): ece += mask.mean() * abs(c[mask].mean() - y[mask].mean())
    return float(ece)
