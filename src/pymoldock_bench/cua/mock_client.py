from ..schemas import Submission

class MockCUAClient:
    """Deterministic offline stand-in; never claims to measure real CUA ability."""
    def __init__(self, outcome: str = "completed", artifacts: dict[str, bytes] | None = None):
        if outcome not in {"completed", "failed", "needs_input", "timeout"}: raise ValueError("unsupported mock outcome")
        self.outcome, self.artifacts = outcome, artifacts or {}

    def run_episode(self, episode, submission: Submission) -> Submission:
        if submission.episode_id != episode.episode_id:
            raise ValueError("submission episode_id does not match episode")
        if self.outcome == "completed": return submission
        return submission.model_copy(update={"status": "human_assist_required" if self.outcome == "needs_input" else self.outcome})

    def collect_artifacts(self, output_dir):
        from pathlib import Path
        out=Path(output_dir); out.mkdir(parents=True, exist_ok=True)
        paths=[]
        for name,data in self.artifacts.items():
            p=out/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data); paths.append(p)
        return paths
