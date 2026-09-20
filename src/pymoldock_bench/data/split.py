from __future__ import annotations
import hashlib

def deterministic_split(target_id: str, *, test_fraction: float = 0.2) -> str:
    if not 0 < test_fraction < 1: raise ValueError("test_fraction must be between 0 and 1")
    value = int(hashlib.sha256(target_id.encode()).hexdigest()[:8], 16) / 2**32
    return "test" if value < test_fraction else "dev"
