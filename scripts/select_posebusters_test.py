#!/usr/bin/env python3
"""Freeze a deterministic PoseBusters test-case selection without exposing it."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--count", type=int, default=308)
    args = ap.parse_args()
    cases = sorted(p for p in args.raw_root.iterdir() if p.is_dir())
    if len(cases) < args.count:
        raise SystemExit(f"need {args.count} cases, found {len(cases)}")
    selected = cases[: args.count]
    rows = [{"rank": i, "case_id": p.name, "source": str(p)} for i, p in enumerate(selected, 1)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"version": "1.0", "count": len(rows), "cases": rows}, indent=2) + "\n")
    print(f"selected={len(rows)} output={args.output}")


if __name__ == "__main__":
    main()
