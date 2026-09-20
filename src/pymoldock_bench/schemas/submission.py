from typing import Literal
from pydantic import BaseModel, Field, field_validator

class InteractionPrediction(BaseModel):
    type: Literal["hydrogen_bond", "hydrophobic", "salt_bridge", "pi_stacking", "cation_pi", "metal_coordination", "steric_clash", "other"]
    chain: str | None = None
    residue_number: str | None = None
    residue_name: str | None = None

class Submission(BaseModel):
    schema_version: str = "1.0"
    episode_id: str
    status: Literal["completed", "failed", "timeout", "needs_input", "human_assist_required"] = "completed"
    interface_residues: list[str] = Field(default_factory=list)
    physical_plausibility: Literal["valid", "invalid", "uncertain", "yes", "no"] = "uncertain"
    native_likeness: Literal["likely_correct", "likely_incorrect", "uncertain", "yes", "no"] = "uncertain"
    confidence: float = 0.0
    selected_pose_path: str | None = None
    artifact_paths: list[str] = Field(default_factory=list)
    failure_category: str | None = None
    interactions: list[InteractionPrediction] = Field(default_factory=list)
    selected_pose: str | None = None
    protocol_violation: bool = False

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("confidence must be between 0 and 1")
        return value
