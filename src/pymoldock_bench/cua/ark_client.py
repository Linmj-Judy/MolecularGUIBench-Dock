from __future__ import annotations
import json, subprocess
from pathlib import Path

class ArkCUAError(RuntimeError): pass

class ArkCUAClient:
    def __init__(self, skill_dir: str | Path):
        self.skill_dir = Path(skill_dir)
        self.cli = self.skill_dir / "scripts" / "cua.py"
        if not self.cli.exists(): raise FileNotFoundError(self.cli)
    def run(self, args: list[str], timeout: int | None = None) -> dict:
        p = subprocess.run(["python3", str(self.cli), *args], capture_output=True, text=True, timeout=timeout)
        try: data = json.loads(p.stdout)
        except json.JSONDecodeError as exc: raise ArkCUAError(f"CUA CLI returned non-JSON (exit {p.returncode})") from exc
        if not data.get("ok", False): raise ArkCUAError(str(data.get("error", "unknown CUA error")))
        return data
    def auth_status(self): return self.run(["auth", "status"])
    def model_info(self): return self.run(["model", "get"])

    def cancel_task(self, task_id: str) -> dict:
        return self.run(["task", "cancel", "--task-id", task_id])

    def delegate(self, objective: str) -> dict:
        return self.run(["delegate", "--objective", objective])
