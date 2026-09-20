from __future__ import annotations
import numpy as np
from ..utils.geometry import sdf_coordinates

def box_from_ligand(ligand, padding: float = 12.0, minimum: float = 18.0, maximum: float = 30.0) -> dict:
    """Derive the documented known-pocket box from ligand heavy-atom coordinates."""
    if padding < 0 or minimum <= 0 or maximum < minimum: raise ValueError("invalid box parameters")
    xyz=sdf_coordinates(ligand)
    lo,hi=xyz.min(0),xyz.max(0); size=np.clip(hi-lo+padding, minimum, maximum); center=(hi+lo)/2
    return {"center": tuple(float(x) for x in center), "size": tuple(float(x) for x in size)}
