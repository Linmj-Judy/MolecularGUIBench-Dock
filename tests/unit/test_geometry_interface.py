from pathlib import Path
from pymoldock_bench.eval.geometry_interface import compute_interface

def test_interface_cutoff_and_residue_identity(tmp_path: Path):
    pdb = tmp_path / "p.pdb"
    pdb.write_text("ATOM      1  CA  ALA A   1       0.000   0.000   0.000                          C  \nATOM      2  CA  ALA A  10A      10.000   0.000   0.000                          C  \n")
    sdf = tmp_path / "l.sdf"
    sdf.write_text("x\n\n\n  1  0  0  0  0  0            999 V2000\n    3.5000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0\nM  END\n$$$$\n")
    assert compute_interface(pdb, sdf, 3.5) == {"A:1"}
    assert compute_interface(pdb, sdf, 3.4) == set()
