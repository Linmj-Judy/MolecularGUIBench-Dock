from pymoldock_bench.data.docking_box import box_from_ligand

def test_box_from_ligand(tmp_path):
    p=tmp_path/"l.sdf"; p.write_text("x\n\n\n  2  0  0  0  0  0            999 V2000\n    0.0    0.0    0.0 C   0  0  0  0  0  0  0  0  0  0  0  0\n    2.0    4.0    6.0 C   0  0  0  0  0  0  0  0  0  0  0  0\nM  END\n$$$$\n")
    b=box_from_ligand(p); assert b["center"] == (1.0,2.0,3.0); assert b["size"] == (18.0,18.0,18.0)
