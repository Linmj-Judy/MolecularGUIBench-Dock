from __future__ import annotations
from pathlib import Path

def collect_outputs(root: str | Path) -> list[str]:
    root = Path(root).resolve()
    if not root.exists(): return []
    return [str(p) for p in sorted(root.rglob("*")) if p.is_file() and root in p.resolve().parents]
