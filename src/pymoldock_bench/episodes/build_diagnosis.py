from __future__ import annotations
import json
from pathlib import Path
from ..schemas import Episode

def build_diagnosis_episode(source: str | Path, output: str | Path, *, episode_id: str, target_id: str, split="dev") -> Path:
    data = json.loads(Path(source).read_text(encoding="utf-8"))
    episode = Episode(episode_id=episode_id, target_id=target_id, split=split,
        task="diagnosis", track="vision_only", receptor_path=data["receptor_path"],
        ligand_path=data["ligand_path"], candidate_pose_path=data.get("candidate_pose_path"),
        objective="Inspect the protein-ligand pose, identify interface residues, and diagnose plausibility.")
    out = Path(output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(episode.model_dump_json(indent=2)); return out

