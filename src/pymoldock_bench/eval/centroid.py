from .rmsd import centroid_rmsd
from ..utils.geometry import sdf_coordinates

def ligand_centroid_distance(predicted: str, reference: str) -> float:
    return centroid_rmsd(sdf_coordinates(predicted), sdf_coordinates(reference))

__all__ = ["centroid_rmsd", "ligand_centroid_distance"]
