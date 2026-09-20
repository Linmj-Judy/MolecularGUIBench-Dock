"""Prepare a downloaded PoseBusters paper archive into an indexed raw tree."""
from __future__ import annotations
import hashlib, json, zipfile
from pathlib import Path

POSEBUSTERS_MD5 = "f004ac7c4e68317b5348497d2bb6bee6"

def verify_md5(path: str | Path, expected: str = POSEBUSTERS_MD5) -> bool:
    h = hashlib.md5()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest() == expected

def safe_extract(archive: str | Path, destination: str | Path) -> list[Path]:
    root, out = Path(archive), Path(destination).resolve(); out.mkdir(parents=True, exist_ok=True)
    extracted = []
    try:
        zf = zipfile.ZipFile(root)
        zf.testzip()
    except (zipfile.BadZipFile, OSError) as exc:
        raise ValueError(f"invalid or incomplete PoseBusters archive: {root}") from exc
    with zf:
        for member in zf.infolist():
            target = (out / member.filename).resolve()
            if out not in target.parents and target != out: raise ValueError("archive path traversal")
            zf.extract(member, out); extracted.append(target)
    return extracted

def build_index(root: str | Path, output: str | Path) -> Path:
    root = Path(root); rows = []
    for p in sorted(root.rglob("*")):
        if p.is_file(): rows.append({"path": str(p.relative_to(root)), "suffix": p.suffix.lower(), "size": p.stat().st_size})
    out = Path(output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(rows, indent=2)); return out
