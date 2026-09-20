from __future__ import annotations
import json, subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
import csv, io

@dataclass(frozen=True)
class PoseBustersResult:
    pb_valid: bool | None
    rmsd_le_2a: bool | None
    individual_checks: dict[str, bool | None]
    raw_output: str

def run_posebusters(ligand: str | Path, protein: str | Path, native: str | Path | None = None, *, executable="bust") -> dict:
    """Run the installed PoseBusters CLI and parse its CSV/JSON-like output.

    The evaluator is optional; a missing executable is reported explicitly so a
    missing dependency cannot be mistaken for a passing pose.
    """
    import shutil
    if shutil.which(executable) is None:
        return {"available": False, "status": "dependency_missing"}
    cmd=[executable, str(ligand), "-p", str(protein)]
    if native: cmd += ["-l", str(native)]
    proc=subprocess.run(cmd,capture_output=True,text=True,check=False)
    parsed=parse_posebusters_output(proc.stdout)
    return {"available": True, "status": "pass" if proc.returncode == 0 else "fail",
            "returncode": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-2000:], **asdict(parsed)}

def _bool(value):
    if value is None: return None
    value=str(value).strip().lower()
    if value in {"true","1","yes","pass","passed"}: return True
    if value in {"false","0","no","fail","failed"}: return False
    return None

def parse_posebusters_output(text: str) -> PoseBustersResult:
    """Parse common PoseBusters CSV output without depending on a pinned CLI."""
    checks={}; rows=[]
    try: rows=list(csv.DictReader(io.StringIO(text)))
    except csv.Error: rows=[]
    if rows:
        row=rows[-1]
        for key,value in row.items():
            if key in {"rmsd", "pb_valid", "valid", "mol_pred_loaded"}: continue
            parsed=_bool(value)
            if parsed is not None: checks[key]=parsed
        pb=_bool(row.get("pb_valid", row.get("valid")))
        rmsd_val=row.get("rmsd")
        try: rmsd_le=float(rmsd_val) <= 2.0 if rmsd_val not in {None,""} else None
        except ValueError: rmsd_le=None
        if pb is None and checks: pb=all(checks.values())
        return PoseBustersResult(pb, rmsd_le, checks, text)
    return PoseBustersResult(None, None, checks, text)

class PoseBustersEvaluator:
    def __init__(self, executable="bust"): self.executable=executable
    def evaluate(self, predicted_ligand, native_ligand, receptor) -> PoseBustersResult:
        result=run_posebusters(predicted_ligand, receptor, native_ligand, executable=self.executable)
        if not result.get("available"): return PoseBustersResult(None, None, {}, json.dumps(result))
        return PoseBustersResult(result.get("pb_valid"), result.get("rmsd_le_2a"), result.get("individual_checks", {}), result.get("stdout", ""))
