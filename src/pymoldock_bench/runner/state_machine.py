from enum import StrEnum

class EpisodeStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    NEEDS_INPUT = "needs_input"
    HUMAN_ASSIST_REQUIRED = "human_assist_required"

def classify_outcome(outcome: str) -> EpisodeStatus:
    if outcome == "completed": return EpisodeStatus.COMPLETED
    if outcome == "needs_input": return EpisodeStatus.HUMAN_ASSIST_REQUIRED
    if outcome in {"cancelled", "failed"}: return EpisodeStatus.FAILED
    if outcome == "timeout": return EpisodeStatus.TIMEOUT
    raise ValueError(f"non-terminal outcome: {outcome}")

