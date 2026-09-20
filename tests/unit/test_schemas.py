from pymoldock_bench.schemas import Episode, Submission, GroundTruth
from pymoldock_bench.eval import evaluate

def test_end_to_end_offline():
    e = Episode(episode_id="e1", target_id="t1", split="dev", task="diagnosis", track="vision_only", receptor_path="r.pdb", ligand_path="l.sdf", objective="inspect")
    s = Submission(episode_id="e1", status="completed", interface_residues=["A:1"], physical_plausibility="yes", native_likeness="no")
    g = GroundTruth(episode_id="e1", interface_residues=["A:1"], pb_valid=True, native_like=False)
    r = evaluate(e, s, g)
    assert r.task_success and r.interface_f1 == 1 and r.pb_valid_correct and r.native_like_correct

