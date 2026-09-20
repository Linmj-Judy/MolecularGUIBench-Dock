# Data format

Public episode manifests use `Episode` from `src/pymoldock_bench/schemas` and
contain receptor, ligand, candidate pose, objective, split, and task metadata.
Private ground truth uses `GroundTruth`; native ligands and evaluator-only labels
must remain under `data/private`. Paths are validated before publication.

