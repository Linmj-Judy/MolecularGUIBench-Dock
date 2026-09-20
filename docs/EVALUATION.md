# Evaluation

Phase A computes residue-level interface precision, recall, and F1, plus explicit
physical-plausibility and native-likeness correctness. `uncertain` predictions
remain visible in the submission and are not silently converted to false.
Coordinate metrics use centroid distance and Kabsch-aligned RMSD. PoseBusters and
ProLIF integrations are optional backends and are only run when installed.

