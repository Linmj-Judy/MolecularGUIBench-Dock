from __future__ import annotations
import time
from ..cua.ark_client import ArkCUAClient
from .state_machine import classify_outcome
from ..schemas import EvaluationResult, Submission
from ..data.isolation import stage_public_tree
from ..data.audit import audit_episode_public_metadata
from ..eval.diagnosis import evaluate

def run_task(client: ArkCUAClient, desktop: str, objective: str, poll_seconds=5, timeout_seconds=1800):
    started = time.monotonic()
    launch = client.run(["task", "run", "--desktop", desktop, "--objective", objective, "--wait-ms", "0"])
    data = launch.get("data", {})
    task_id = data.get("task_id") or data.get("invocation_id") or data.get("id")
    if not task_id: raise RuntimeError("CUA response did not contain a task id")
    while time.monotonic() - started < timeout_seconds:
        status = client.run(["task", "status", "--task-id", task_id])
        current = status.get("data", {})
        outcome = current.get("outcome")
        if outcome in {"completed", "needs_input", "failed", "cancelled", "timeout"}:
            result = None
            if outcome == "completed":
                # The result command is authoritative for completed tasks; status
                # alone may contain only progress metadata.
                result = client.run(["task", "result", "--task-id", task_id, "--timeout", "1"])
            return {"task_id": task_id, "status": classify_outcome(outcome).value, "raw": status, "result": result,
                    "autonomous_success": outcome == "completed", "human_assistance_required": outcome == "needs_input"}
        time.sleep(min(poll_seconds, max(0.25, timeout_seconds / 20)))
    cancel = None
    try: cancel = client.cancel_task(task_id)
    except Exception as exc: cancel = {"error": type(exc).__name__}
    return {"task_id": task_id, "status": "timeout", "cancel": cancel,
            "autonomous_success": False, "human_assistance_required": False}

class EpisodeRunner:
    """Offline-first controller; real Ark clients can be supplied separately."""
    def __init__(self, client, public_root=None, staging_root=None):
        self.client, self.public_root, self.staging_root = client, public_root, staging_root

    def run(self, episode, *, submission: Submission | None = None, ground_truth=None, output_dir=None):
        try:
            if self.public_root and self.staging_root:
                source = __import__("pathlib").Path(self.public_root) / episode.episode_id
                staged = stage_public_tree(source, self.staging_root, __import__("pathlib").Path(self.public_root).parent / "private")
                findings = audit_episode_public_metadata(staged)
                if findings: raise ValueError(f"public metadata leakage: {findings[:3]}")
            if submission is None:
                submission = Submission(episode_id=episode.episode_id, status="completed")
            result = evaluate(episode, submission, ground_truth) if ground_truth else EvaluationResult(
                episode_id=episode.episode_id, task_success=submission.status == "completed",
                cua_outcome=submission.status, autonomous_success=submission.status == "completed",
                human_assistance_required=submission.status == "human_assist_required",
                submission_present=True, confidence=submission.confidence)
            if output_dir:
                from .logging import write_json
                write_json(__import__("pathlib").Path(output_dir) / "evaluation.json", result.model_dump())
            return result
        except Exception as exc:
            return EvaluationResult(episode_id=episode.episode_id, cua_outcome="failed", failure_category=type(exc).__name__)
