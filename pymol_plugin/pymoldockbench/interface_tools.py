def create_interface_selection(cmd, selection="byres ligand around 4.0", name="agent_interface"):
    """Create a residue selection around ligand and return its count."""
    return int(cmd.select(name, selection))

