"""Small, deterministic subprocess boundary for AutoDock Vina."""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path

class VinaBackend:
    def __init__(self, executable="vina", *, exhaustiveness=16, num_modes=10, energy_range=5, seed=20260920, cpu=4):
        self.executable = executable
        self.params = {"exhaustiveness": exhaustiveness, "num_modes": num_modes, "energy_range": energy_range, "seed": seed, "cpu": cpu}
        if any(int(v) <= 0 for v in self.params.values()): raise ValueError("Vina parameters must be positive")
    def available(self): return shutil.which(self.executable) is not None
    def run(self, receptor: str | Path, ligand: str | Path, output: str | Path, *, center: tuple[float,float,float], size: tuple[float,float,float], timeout: int = 1800) -> Path:
        if not self.available(): raise FileNotFoundError(f"Vina executable not found: {self.executable}")
        if len(center) != 3 or len(size) != 3 or any(float(x) <= 0 for x in size): raise ValueError("invalid docking box")
        out = Path(output); out.parent.mkdir(parents=True, exist_ok=True)
        cmd = [self.executable, "--receptor", str(receptor), "--ligand", str(ligand), "--out", str(out)]
        for key, value in (("center_x", center[0]), ("center_y", center[1]), ("center_z", center[2]), ("size_x", size[0]), ("size_y", size[1]), ("size_z", size[2]), *self.params.items()): cmd += [f"--{key}", str(value)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        if proc.returncode: raise RuntimeError(f"Vina failed with exit {proc.returncode}: {proc.stderr[-1000:]}")
        return out
