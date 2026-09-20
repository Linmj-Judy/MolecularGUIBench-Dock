from pathlib import Path
from .anonymize import anonymize_pdb

def sanitize_pdb(src: str | Path, dst: str | Path) -> None:
    Path(dst).parent.mkdir(parents=True, exist_ok=True); Path(dst).write_text(anonymize_pdb(Path(src).read_text()))
