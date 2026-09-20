import re
from pathlib import Path
from ..utils.geometry import stable_rotation_translation

_DROP = re.compile(r"^(HEADER|TITLE|COMPND|SOURCE|DBREF|JRNL|REMARK)")
def anonymize_pdb(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not _DROP.match(line)) + "\n"
def anonymize_file(src: str | Path, dst: str | Path) -> None:
    Path(dst).write_text(anonymize_pdb(Path(src).read_text()), encoding="utf-8")

def anonymize_sdf(text: str) -> str:
    """Remove SD properties while preserving the mol block and chemistry."""
    lines=text.splitlines(); kept=[]; i=0
    while i < len(lines):
        if lines[i].startswith(">"):
            i += 1
            while i < len(lines) and lines[i] != "": i += 1
            if i < len(lines): i += 1
            continue
        kept.append(lines[i]); i += 1
    return "\n".join(kept).rstrip()+"\n"

def rigid_transform_pdb(text: str, seed: str) -> str:
    rotation, translation = stable_rotation_translation(seed)
    output=[]
    for line in text.splitlines():
        if line[:6].strip() not in {"ATOM", "HETATM"}:
            output.append(line); continue
        try:
            xyz=rotation @ [float(line[30:38]),float(line[38:46]),float(line[46:54])] + translation
            output.append(f"{line[:30]}{xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}{line[54:]}")
        except ValueError: output.append(line)
    return "\n".join(output)+"\n"
