"""Headless PyMOL selection extraction, optional at runtime."""
from pathlib import Path

def extract_selection_from_pse(pse_path: str | Path, selection_name: str = "agent_interface") -> set[str]:
    try:
        from pymol import cmd
    except ImportError as exc:
        raise RuntimeError("PyMOL is not installed") from exc
    cmd.reinitialize()
    cmd.load(str(pse_path), "session")
    if selection_name not in set(cmd.get_names("selections")): return set()
    return {f"{a.chain or '_'}:{a.resi}{a.inscode or ''}" for a in cmd.get_model(selection_name).atom}
