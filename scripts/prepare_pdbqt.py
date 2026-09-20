#!/usr/bin/env python3
"""Prepare Vina inputs using the installed Meeko command-line tools.

The script deliberately fails closed when receptor preparation dependencies are
missing; it never writes a guessed PDBQT file.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def run() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("receptor", type=Path)
    ap.add_argument("ligand", type=Path)
    ap.add_argument("output_dir", type=Path)
    args = ap.parse_args()
    receptor_tool = shutil.which("mk_prepare_receptor.py")
    ligand_tool = shutil.which("mk_prepare_ligand.py")
    if not receptor_tool or not ligand_tool:
        raise SystemExit("Meeko tools missing; install meeko and gemmi first")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    receptor_prefix = args.output_dir / "receptor"
    ligand_output = args.output_dir / "ligand.pdbqt"
    with tempfile.TemporaryDirectory() as td:
        # Meeko requires explicit hydrogens for reliable ligand typing.
        prepared_ligand = Path(td) / "ligand.sdf"
        from rdkit import Chem
        from rdkit.Chem import AddHs
        mol = Chem.SDMolSupplier(str(args.ligand), removeHs=False)[0]
        if mol is None:
            raise SystemExit(f"cannot read ligand: {args.ligand}")
        writer = Chem.SDWriter(str(prepared_ligand))
        writer.write(AddHs(mol)); writer.close()
        subprocess.run([ligand_tool, "-i", str(prepared_ligand), "-o", str(ligand_output)], check=True)
    subprocess.run([receptor_tool, "-i", str(args.receptor), "-o", str(receptor_prefix), "-p"], check=True)
    print(receptor_prefix.with_suffix(".pdbqt"))
    print(ligand_output)


if __name__ == "__main__":
    run()
