from pymoldock_bench.schemas import Episode, Submission
from pymoldock_bench.runner.episode_runner import EpisodeRunner
from pymoldock_bench.cua.mock_client import MockCUAClient

def test_offline_episode_runner(tmp_path):
    public=tmp_path/"public"; case=public/"E1"; case.mkdir(parents=True)
    (case/"episode.json").write_text('{}'); (case/"receptor.pdb").write_text('ATOM')
    e=Episode(episode_id="E1",target_id="T1",split="dev",task="diagnosis",track="vision_only",receptor_path="r",ligand_path="l")
    s=Submission(episode_id="E1",status="completed")
    r=EpisodeRunner(MockCUAClient(), public, tmp_path/"stage").run(e, submission=s)
    assert r.task_success
