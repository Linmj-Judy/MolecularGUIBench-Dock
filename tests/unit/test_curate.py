from pymoldock_bench.data.curate import curate_case

def test_curate_exposes_only_public_files(tmp_path):
    case=tmp_path/"case"; case.mkdir(); (case/"protein.pdb").write_text("ATOM"); (case/"ligand.sdf").write_text("mol")
    manifest=curate_case(case,tmp_path/"public",episode_id="e1",target_id="t1")
    assert manifest.exists() and (manifest.parent/"receptor.pdb").exists() and (manifest.parent/"ligand.sdf").exists()

