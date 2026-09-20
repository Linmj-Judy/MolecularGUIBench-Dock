from pydantic import BaseModel, Field

class EvaluationResult(BaseModel):
    episode_id: str
    interface_precision: float = 0.0
    interface_recall: float = 0.0
    interface_f1: float = 0.0
    pb_valid_correct: bool | None = None
    native_like_correct: bool | None = None
    task_success: bool = False
    metrics: dict[str, float] = Field(default_factory=dict)
    cua_outcome: str = "completed"
    autonomous_success: bool = False
    human_assistance_required: bool = False
    runtime_sec: float | None = None
    submission_present: bool = False
    final_pse_present: bool = False
    agent_observed_interface_jaccard: float | None = None
    candidate_native_interface_f1: float | None = None
    centroid_distance: float | None = None
    pb_valid: bool | None = None
    confidence: float | None = None
    failure_category: str | None = None
    protocol_violation: bool = False

EpisodeResult = EvaluationResult
