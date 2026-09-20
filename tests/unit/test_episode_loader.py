import json
from pathlib import Path
from pymoldockbench.episode_loader import load_into_pymol

class Cmd:
    def __init__(self): self.calls=[]
    def reinitialize(self): self.calls.append(("reinitialize",))
    def load(self,*x): self.calls.append(("load",)+x)
    def hide(self,*x): self.calls.append(("hide",)+x)
    def show(self,*x): self.calls.append(("show",)+x)
    def orient(self,*x): self.calls.append(("orient",)+x)

def test_loader_applies_scene_defaults(tmp_path: Path):
    e={"episode_id":"E1","receptor_path":"r.pdb","ligand_path":"l.sdf"}
    p=tmp_path/"e.json"; p.write_text(json.dumps(e)); c=Cmd()
    loaded=load_into_pymol(p,c)
    assert loaded["camera_seed"] == load_into_pymol(p,Cmd())["camera_seed"]
    assert ("show","cartoon","receptor") in c.calls
