import json
from pymoldock_bench.episodes.build_diagnosis import build_diagnosis_episode

def test_build_episode(tmp_path):
    src = tmp_path / "source.json"; src.write_text(json.dumps({"receptor_path":"r.pdb","ligand_path":"l.sdf"}))
    out = build_diagnosis_episode(src, tmp_path / "e.json", episode_id="e1", target_id="t1")
    assert json.loads(out.read_text())["task"] == "diagnosis"

