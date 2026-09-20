from pymoldock_bench.data.curate import curate_case

def test_curate_prefixed_astex_names(tmp_path):
    case=tmp_path/"1VCJ_IBA"; case.mkdir()
    (case/"1VCJ_IBA_protein.pdb").write_text("HEADER secret\nATOM")
    (case/"1VCJ_IBA_ligand.sdf").write_text("name\n\n\n  0  0  0  0  0  0            999 V2000\nM  END\n$$$$\n")
    out=curate_case(case,tmp_path/"public",episode_id="ASTEX_0001",target_id="1VCJ_IBA")
    assert out.exists() and (out.parent/"receptor.pdb").exists()
