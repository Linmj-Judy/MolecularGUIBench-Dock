from pathlib import Path

def export_session(cmd, output: str | Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd.save(str(output))

