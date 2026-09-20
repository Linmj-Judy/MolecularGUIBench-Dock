"""Dependency-light structure geometry used by the offline evaluator."""
from __future__ import annotations
import hashlib
from pathlib import Path
import numpy as np

def _text(source):
    if isinstance(source, Path): return source.read_text()
    if isinstance(source, str):
        p=Path(source)
        if len(source) < 4096 and p.exists(): return p.read_text()
    return str(source)

def pdb_atoms(source: str | Path):
    text = _text(source)
    out = []
    for line in text.splitlines():
        if line[:6].strip() not in {"ATOM", "HETATM"}: continue
        element = (line[76:78].strip() or line[12:14].strip()[0]).upper()
        try: xyz = np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])])
        except ValueError: continue
        out.append({"element": element, "coord": xyz, "chain": line[21].strip() or "_", "resi": line[22:26].strip(), "icode": line[26].strip(), "record": line[:6].strip()})
    return out

def sdf_coordinates(source: str | Path) -> np.ndarray:
    text = _text(source)
    lines = text.splitlines()
    if len(lines) < 4: raise ValueError("invalid SDF")
    try: n = int(lines[3][:3])
    except ValueError: raise ValueError("invalid SDF counts line")
    coords = []
    for line in lines[4:4+n]:
        try: coords.append([float(line[:10]), float(line[10:20]), float(line[20:30])])
        except ValueError:
            try: coords.append([float(x) for x in line.split()[:3]])
            except (ValueError, IndexError): continue
    if len(coords) != n: raise ValueError("invalid SDF atom coordinates")
    return np.asarray(coords, dtype=float)

def stable_rotation_translation(seed: str, translation_scale: float = 50.0):
    digest = hashlib.sha256(seed.encode()).digest()
    rng = np.random.default_rng(int.from_bytes(digest[:8], "big"))
    q = rng.normal(size=4); q /= np.linalg.norm(q)
    w,x,y,z=q
    rotation=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    return rotation, rng.uniform(-translation_scale, translation_scale, size=3)

def transform_coordinates(coords: np.ndarray, rotation: np.ndarray, translation: np.ndarray) -> np.ndarray:
    a=np.asarray(coords,float)
    if a.ndim != 2 or a.shape[1] != 3: raise ValueError("coords must have shape (N,3)")
    return a @ rotation.T + translation
