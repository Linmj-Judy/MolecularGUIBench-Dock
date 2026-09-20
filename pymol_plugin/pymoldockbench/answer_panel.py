"""Optional PyMOL GUI bridge for writing a structured submission."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_submission(payload: dict[str, Any], path: str | Path) -> Path:
    """Write JSON supplied by the panel without attempting to infer answers."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output
