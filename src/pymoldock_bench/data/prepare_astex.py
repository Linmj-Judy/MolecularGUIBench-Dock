from pathlib import Path
from .curate import curate_case

def prepare_astex(raw_root: str | Path, public_root: str | Path, limit: int | None = None, *, split: str = "dev") -> list[Path]:
    if split not in {"dev", "test"}: raise ValueError("split must be dev or test")
    cases = [p for p in sorted(Path(raw_root).iterdir()) if p.is_dir()]
    if limit is not None: cases = cases[:limit]
    outputs=[]
    for i, case in enumerate(cases, 1):
        try:
            path=curate_case(case, public_root, episode_id=f"ASTEX_{i:04d}", target_id=f"ASTEX_{i:04d}")
            import json
            data=json.loads(path.read_text()); data["split"]=split; path.write_text(json.dumps(data, indent=2)); outputs.append(path)
        
        except FileNotFoundError: continue
    return outputs
