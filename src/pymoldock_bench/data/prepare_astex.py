from pathlib import Path
from .curate import curate_case

def prepare_astex(raw_root: str | Path, public_root: str | Path, limit: int | None = None) -> list[Path]:
    cases = [p for p in sorted(Path(raw_root).iterdir()) if p.is_dir()]
    if limit is not None: cases = cases[:limit]
    outputs=[]
    for i, case in enumerate(cases, 1):
        try: outputs.append(curate_case(case, public_root, episode_id=f"ASTEX_{i:04d}", target_id=f"ASTEX_{i:04d}"))
        except FileNotFoundError: continue
    return outputs
