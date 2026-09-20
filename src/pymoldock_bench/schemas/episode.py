from typing import Literal
from pydantic import BaseModel, Field, model_validator

class DockingBox(BaseModel):
    center: tuple[float, float, float]
    size: tuple[float, float, float]

class Episode(BaseModel):
    schema_version: str = "1.0"
    episode_id: str
    target_id: str
    split: Literal["dev", "test"]
    task: Literal["gui", "interface", "interaction", "diagnosis", "ranking", "redocking"]
    track: Literal["vision_only", "tool_assisted", "workflow"]
    public_dir: str | None = None
    receptor_path: str | None = None
    receptor_file: str | None = None
    ligand_path: str | None = None
    ligand_file: str | None = None
    candidate_pose_path: str | None = None
    docking_box: DockingBox | None = None
    max_walltime_sec: int = 1800
    expected_artifacts: list[str] = Field(default_factory=list)
    prompt_template: str | None = None
    objective: str = "Inspect the protein-ligand pose and submit a diagnosis."
    seed: int = 0
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_paths(self):
        if self.receptor_path is None: self.receptor_path = self.receptor_file
        if self.ligand_path is None: self.ligand_path = self.ligand_file
        if self.receptor_path is None:
            raise ValueError("receptor_path or receptor_file is required")
        if self.ligand_path is None and self.candidate_pose_path is None:
            raise ValueError("ligand_path or candidate_pose_path is required")
        if self.max_walltime_sec <= 0:
            raise ValueError("max_walltime_sec must be positive")
        return self
