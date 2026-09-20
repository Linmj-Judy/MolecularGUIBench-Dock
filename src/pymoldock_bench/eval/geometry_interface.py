from __future__ import annotations
import numpy as np
from ..utils.geometry import pdb_atoms, sdf_coordinates

def compute_interface(protein: str, ligand: str, cutoff: float = 4.0) -> set[str]:
    """Return chain:residue[insertion] for protein residues within cutoff of ligand."""
    if cutoff <= 0: raise ValueError("cutoff must be positive")
    atoms=[a for a in pdb_atoms(protein) if a["record"] == "ATOM" and a["element"] != "H"]
    lig=sdf_coordinates(ligand)
    if not len(atoms) or not len(lig): return set()
    l=lig[np.newaxis,:,:]; result=set()
    for atom in atoms:
        if np.min(np.linalg.norm(l[0]-atom["coord"],axis=1)) <= cutoff:
            result.add(f'{atom["chain"]}:{atom["resi"]}{atom["icode"]}')
    return result
