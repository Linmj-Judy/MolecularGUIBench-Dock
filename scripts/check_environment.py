#!/usr/bin/env python3
import importlib.util, shutil, sys
print(f"python={sys.version.split()[0]}")
print(f"pymol={bool(shutil.which('pymol'))}")
print(f"vina={bool(shutil.which('vina'))}")
print(f"arkcli={bool(shutil.which('arkcli'))}")
for name in ("pydantic", "numpy", "yaml"):
    print(f"{name}={bool(importlib.util.find_spec(name))}")

