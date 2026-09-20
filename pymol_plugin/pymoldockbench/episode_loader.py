"""Small PyMOL-facing loader; imports lazily so the package is testable off-PyMOL."""
import json
from pathlib import Path
import hashlib

def load_episode(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {"episode_id", "receptor_path", "ligand_path"}
    missing = required - data.keys()
    if missing: raise ValueError(f"episode missing fields: {sorted(missing)}")
    return data

def load_into_pymol(episode_path: str | Path, cmd=None) -> dict:
    episode = load_episode(episode_path)
    if cmd is None:
        try: from pymol import cmd
        except ImportError as exc: raise RuntimeError("PyMOL is required to load an episode") from exc
    cmd.reinitialize()
    cmd.load(episode["receptor_path"], "receptor")
    cmd.load(episode["ligand_path"], "ligand")
    if episode.get("candidate_pose_path"): cmd.load(episode["candidate_pose_path"], "candidate_pose")
    cmd.hide("everything", "all")
    cmd.show("cartoon", "receptor")
    cmd.show("sticks", "ligand or candidate_pose")
    cmd.hide("everything", "solvent")
    # Stable orientation metadata; PyMOL applies the actual view when available.
    seed = int.from_bytes(hashlib.sha256(episode["episode_id"].encode()).digest()[:4], "big")
    if hasattr(cmd, "orient"): cmd.orient("receptor")
    episode["camera_seed"] = seed
    return episode
