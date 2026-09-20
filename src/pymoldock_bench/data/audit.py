from __future__ import annotations
import re
from pathlib import Path

_MARKERS = re.compile(r"(?:native|ground[_ -]?truth|crystal[_ -]?pose|rmsd|pb[-_ ]?valid|pose[_ -]?bucket|docking[_ -]?score|pdb[_ -]?id)", re.I)

def audit_episode_public_metadata(root: str | Path) -> list[str]:
    """Return leakage findings; callers should fail closed when non-empty."""
    findings=[]; root=Path(root)
    for p in root.rglob("*"):
        if _MARKERS.search(p.name): findings.append(str(p))
        if p.is_file() and p.stat().st_size < 5_000_000:
            try:
                for n,line in enumerate(p.read_text(errors="ignore").splitlines(),1):
                    if _MARKERS.search(line): findings.append(f"{p}:{n}")
            except OSError: pass
    return sorted(set(findings))
