"""Create public episode manifests from a raw PoseBusters-style tree.

The curator copies only receptor/candidate files and deliberately never copies
native labels or evaluator metadata into the public tree.
"""
from __future__ import annotations
import json, shutil
from pathlib import Path
from .anonymize import anonymize_pdb, anonymize_sdf

def _first(root: Path, names: tuple[str, ...]) -> Path | None:
    for p in sorted(root.rglob("*")):
        lower=p.name.lower()
        if p.is_file() and (lower in names or any(lower.endswith("_" + name) for name in names)):
            return p
    return None

def curate_case(case_root: str | Path, public_root: str | Path, *, episode_id: str, target_id: str) -> Path:
    case, out = Path(case_root), Path(public_root) / episode_id
    receptor = _first(case, ("protein.pdb", "receptor.pdb", "protein.mol2"))
    ligand = _first(case, ("ligand.sdf", "ligand.mol2", "ligand.mol", "ligand_reference.mol2"))
    if receptor is None or ligand is None: raise FileNotFoundError("case requires receptor and ligand")
    out.mkdir(parents=True, exist_ok=True)
    receptor_dst = (out / "receptor").with_suffix(Path(receptor).suffix)
    ligand_dst = (out / "ligand").with_suffix(Path(ligand).suffix)
    if receptor.suffix.lower() == ".pdb": receptor_dst.write_text(anonymize_pdb(receptor.read_text()), encoding="utf-8")
    else: shutil.copyfile(receptor, receptor_dst)
    if ligand.suffix.lower() in {".sdf", ".mol"}: ligand_dst.write_text(anonymize_sdf(ligand.read_text()), encoding="utf-8")
    else: shutil.copyfile(ligand, ligand_dst)
    manifest = {"schema_version":"1.0", "episode_id":episode_id, "target_id":target_id,
      "split":"dev", "task":"diagnosis", "track":"vision_only",
      "receptor_path":str(receptor_dst), "ligand_path":str(ligand_dst),
      "objective":"Inspect the protein-ligand pose and identify the interface."}
    path = out / "episode.json"; path.write_text(json.dumps(manifest, indent=2)); return path
