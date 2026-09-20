from __future__ import annotations
from pathlib import Path

def collect_outputs(root: str | Path) -> list[str]:
    root = Path(root).resolve()
    if not root.exists(): return []
    return [str(p) for p in sorted(root.rglob("*")) if p.is_file() and root in p.resolve().parents]

def collect_expected(root: str | Path, expected: list[str], destination: str | Path) -> list[Path]:
    """Copy registered artifacts without following workspace escapes or overwriting."""
    import shutil
    base=Path(root).resolve(); dest=Path(destination).resolve(); dest.mkdir(parents=True, exist_ok=True); output=[]
    for name in expected:
        source=(base/name).resolve()
        if base not in source.parents or not source.is_file(): continue
        target=dest/Path(name).name
        if target.exists(): raise FileExistsError(f"refusing to overwrite artifact: {target}")
        shutil.copyfile(source,target); output.append(target)
    return output
