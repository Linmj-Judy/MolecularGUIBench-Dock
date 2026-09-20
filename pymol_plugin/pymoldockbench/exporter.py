from pathlib import Path
import shutil

def export_session(cmd, output: str | Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd.save(str(output))

def export_selected_pose(source: str | Path, output: str | Path, workspace: str | Path) -> Path:
    source=Path(source).resolve(); root=Path(workspace).resolve(); output=Path(output)
    if root not in source.parents or not source.is_file(): raise ValueError("selected pose is outside public workspace")
    if output.exists(): raise FileExistsError(f"refusing to overwrite {output}")
    output.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, output); return output
