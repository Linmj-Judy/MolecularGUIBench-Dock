import numpy as np
import itertools

def centroid(coords: np.ndarray) -> np.ndarray:
    a = np.asarray(coords, dtype=float)
    if a.ndim != 2 or a.shape[1] != 3 or len(a) == 0:
        raise ValueError("coords must be a non-empty (N, 3) array")
    return a.mean(axis=0)

def centroid_rmsd(predicted: np.ndarray, reference: np.ndarray) -> float:
    return float(np.linalg.norm(centroid(predicted) - centroid(reference)))

def kabsch_rmsd(predicted: np.ndarray, reference: np.ndarray) -> float:
    p, q = np.asarray(predicted, float), np.asarray(reference, float)
    if p.shape != q.shape or p.ndim != 2 or p.shape[1] != 3 or not len(p):
        raise ValueError("coordinate arrays must have equal non-empty shape (N, 3)")
    pc, qc = p - p.mean(0), q - q.mean(0)
    u, _, vt = np.linalg.svd(pc.T @ qc)
    d = np.sign(np.linalg.det(u @ vt))
    rot = u @ np.diag([1.0, 1.0, d]) @ vt
    return float(np.sqrt(np.mean(np.sum((pc @ rot - qc) ** 2, axis=1))))

def symmetry_aware_rmsd(predicted: np.ndarray, reference: np.ndarray, atom_groups=None) -> float:
    """Minimum aligned RMSD over equivalent atom permutations.

    ``atom_groups`` is a sequence of index groups known to be chemically
    equivalent. Without it, coordinates are treated as already graph-mapped.
    The bounded permutation fallback keeps this dependency-free for CI; RDKit
    can supply graph mappings in production.
    """
    p, q = np.asarray(predicted, float), np.asarray(reference, float)
    if p.shape != q.shape: raise ValueError("coordinate arrays must have equal shape")
    groups = atom_groups or []
    if not groups: return kabsch_rmsd(p, q)
    perms=[list(itertools.permutations(g)) for g in groups]
    best=float("inf")
    for choices in itertools.product(*perms):
        mapping=list(range(len(q)))
        for group, perm in zip(groups, choices):
            for dst, src in zip(group, perm): mapping[dst]=src
        best=min(best, kabsch_rmsd(p, q[mapping]))
    return best
