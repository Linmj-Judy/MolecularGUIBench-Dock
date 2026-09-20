from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class PoseCandidate:
    path: Path
    label: str

def discover_poses(root: str | Path) -> list[PoseCandidate]:
    root = Path(root)
    return [PoseCandidate(p, "candidate") for p in sorted(root.rglob("*.sdf")) if p.is_file()]
