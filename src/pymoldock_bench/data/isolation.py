from pathlib import Path

FORBIDDEN_NAMES = {"native", "ground_truth", "gt.json", "reference_pose", "crystal_ligand"}

def assert_public_path(path: str | Path, root: str | Path) -> None:
    p, r = Path(path).resolve(), Path(root).resolve()
    if r not in p.parents and p != r: raise ValueError(f"path is outside public root: {p}")
    # macOS temporary paths themselves commonly begin with /private; only a
    # nested data/private component is a benchmark private-data marker.
    if any(part.lower() == "private" for part in p.parts[2:]): raise ValueError("private data cannot be exposed")

def assert_private_data_not_exposed(staged_root: str | Path, private_root: str | Path | None = None) -> None:
    """Fail closed if a staged CUA tree contains obvious GT files or private symlinks."""
    staged = Path(staged_root).resolve()
    private = Path(private_root).resolve() if private_root else None
    if not staged.is_dir():
        raise ValueError(f"staging root does not exist: {staged}")
    for item in staged.rglob("*"):
        if item.name.lower() in FORBIDDEN_NAMES or any(part.lower() in FORBIDDEN_NAMES for part in item.parts):
            raise ValueError(f"ground-truth marker in staged tree: {item}")
        if item.is_symlink():
            target = item.resolve()
            if private and (target == private or private in target.parents):
                raise ValueError(f"symlink points into private data: {item}")
            if not (target == staged or staged in target.parents):
                raise ValueError(f"staged symlink escapes root: {item}")

def stage_public_tree(source_root: str | Path, destination: str | Path, private_root: str | Path | None = None) -> Path:
    """Copy a public staging tree and validate it before a CUA task starts."""
    import shutil
    source, dest = Path(source_root).resolve(), Path(destination).resolve()
    assert_public_path(source, source.parent)
    if not source.is_dir():
        raise ValueError("source public tree must be a directory")
    if dest.exists():
        raise FileExistsError(f"refusing to overwrite staging tree: {dest}")
    shutil.copytree(source, dest, symlinks=True)
    assert_private_data_not_exposed(dest, private_root)
    return dest
