#!/usr/bin/env python3
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

def main():
    skill = Path(__file__).resolve().parents[1] / ".agents/skills/byted-util-ark-cua"
    checks = {
        "python": sys.version.split()[0],
        "pymol": bool(shutil.which("pymol")),
        "vina": bool(shutil.which("vina")),
        "posebusters": bool(shutil.which("bust")),
        "arkcli": bool(shutil.which("arkcli")),
        "rdkit": bool(importlib.util.find_spec("rdkit")),
        "pydantic": bool(importlib.util.find_spec("pydantic")),
        "numpy": bool(importlib.util.find_spec("numpy")),
        "yaml": bool(importlib.util.find_spec("yaml")),
        "cua_skill": skill.exists(),
    }
    if skill.exists():
        proc = subprocess.run(["python3", str(skill / "scripts/cua.py"), "auth", "status"], capture_output=True, text=True, check=False)
        try:
            payload = json.loads(proc.stdout)
            checks["ark_auth"] = "ready" if payload.get("ok") else payload.get("error", {}).get("code", "unavailable")
        except json.JSONDecodeError:
            checks["ark_auth"] = "unavailable"
    print(json.dumps(checks, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
