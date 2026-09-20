from pydantic import BaseModel, Field

class GroundTruth(BaseModel):
    schema_version: str = "1.0"
    episode_id: str
    target_id: str | None = None
    native_ligand_path: str | None = None
    native_complex_path: str | None = None
    receptor_path: str | None = None
    interface_residues: list[str] = Field(default_factory=list)
    pb_valid: bool | None = None
    native_like: bool | None = None
    ligand_rmsd: float | None = None
    centroid_rmsd: float | None = None
    native_interface: list[str] = Field(default_factory=list)
    candidate_interface: list[str] = Field(default_factory=list)
    candidate_native_interface_f1: float | None = None
    pose_bucket: str | None = None
