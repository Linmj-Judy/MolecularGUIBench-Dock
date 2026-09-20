from __future__ import annotations
import json, subprocess
from pathlib import Path

class ArkCUAError(RuntimeError): pass
class ArkCUAAuthRequired(ArkCUAError): pass

class ArkCUAClient:
    def __init__(self, skill_dir: str | Path):
        self.skill_dir = Path(skill_dir)
        self.cli = self.skill_dir / "scripts" / "cua.py"
        if not self.cli.exists(): raise FileNotFoundError(self.cli)
    def run(self, args: list[str], timeout: int | None = None) -> dict:
        p = subprocess.run(["python3", str(self.cli), *args], capture_output=True, text=True, timeout=timeout)
        try: data = json.loads(p.stdout)
        except json.JSONDecodeError as exc: raise ArkCUAError(f"CUA CLI returned non-JSON (exit {p.returncode})") from exc
        if not data.get("ok", False):
            error=data.get("error", {})
            code=error.get("code") if isinstance(error, dict) else None
            message=error.get("message", "unknown CUA error") if isinstance(error, dict) else str(error)
            if code in {"AUTH_REQUIRED", "TOKEN_EXPIRED", "REFRESH_FAILED"}:
                raise ArkCUAAuthRequired(code)
            raise ArkCUAError(f"{code or 'CUA_ERROR'}: {message}")
        return data
    def auth_status(self): return self.run(["auth", "status"])
    def model_info(self): return self.run(["model", "get"])

    def environment_info(self):
        """Return non-secret model and authentication metadata for run manifests."""
        return {"model": self.model_info(), "auth": self.auth_status()}

    def cancel_task(self, task_id: str) -> dict:
        return self.run(["task", "cancel", "--task-id", task_id])

    def delegate(self, objective: str) -> dict:
        return self.run(["delegate", "--objective", objective])
