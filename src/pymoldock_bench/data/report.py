from __future__ import annotations
import csv
import json
from collections import Counter
from pathlib import Path

def build_dataset_report(manifest_root: str | Path) -> dict:
    root=Path(manifest_root); rows=[]; excluded=[]
    for p in sorted(root.rglob("episode.json")):
        try: rows.append(json.loads(p.read_text()))
        except Exception as exc: excluded.append({"path":str(p),"reason":f"invalid_manifest:{type(exc).__name__}"})
    buckets=Counter(r.get("pose_bucket") for r in rows if r.get("pose_bucket"))
    return {"targets_total":len({r.get("target_id") for r in rows}), "targets_usable":len(rows), "poses_total":len(rows), "excluded_count":len(excluded), "exclude_reasons":excluded, "pose_buckets":dict(buckets)}

def write_dataset_report(manifest_root: str | Path, output: str | Path) -> Path:
    report=build_dataset_report(manifest_root); out=Path(output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    csv_path=out.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer=csv.writer(handle); writer.writerow(["metric", "value"])
        for key,value in report.items():
            writer.writerow([key, json.dumps(value) if isinstance(value, (dict,list)) else value])
    return out
