from __future__ import annotations
import hashlib, json, platform, shutil, subprocess, sys
from pathlib import Path

def sha256_file(path: str | Path) -> str:
    h=hashlib.sha256();
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()

def build_run_manifest(config_path: str | Path | None = None, *, root_seed: int = 20260920, skill_path: str | Path | None = None) -> dict:
    def version(command):
        try: return subprocess.run(command, capture_output=True, text=True, timeout=5).stdout.strip().splitlines()[0]
        except Exception: return None
    manifest={"python":sys.version.split()[0],"platform":platform.platform(),"root_seed":root_seed,
              "tools":{"arkcli":version(["arkcli","--version"]),"pymol":shutil.which("pymol"),"vina":shutil.which("vina"),"bust":shutil.which("bust")}}
    if skill_path:
        p=Path(skill_path); manifest["cua_skill"]={"path":str(p),"version":None}
        if (p/"SKILL.md").exists():
            for line in (p/"SKILL.md").read_text(errors="ignore").splitlines():
                if line.startswith("version:"): manifest["cua_skill"]["version"]=line.split(":",1)[1].strip(); break
    if config_path: manifest["config_sha256"]=sha256_file(config_path)
    return manifest

def write_run_manifest(output: str | Path, **kwargs) -> Path:
    out=Path(output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(build_run_manifest(**kwargs),indent=2),encoding="utf-8"); return out
