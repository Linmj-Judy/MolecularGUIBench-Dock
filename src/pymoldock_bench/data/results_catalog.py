from __future__ import annotations
import csv
from pathlib import Path

def read_results_catalog(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as f: return list(csv.DictReader(f))

def summarize_catalog(path: str | Path) -> dict[str, int]:
    rows = read_results_catalog(path)
    return {"rows": len(rows), "columns": len(rows[0]) if rows else 0}
