# Evaluation

Primary evaluation is deterministic and uses structured submissions, PyMOL
selections, coordinate geometry, and PoseBusters output. Free-form reasoning is
stored for audit but is never used as a primary judge.

For predicted residue set `I_p` and reference set `I_g`:

```text
P = |I_p ∩ I_g| / |I_p|
R = |I_p ∩ I_g| / |I_g|
F1 = 2PR / (P + R)
Jaccard = |I_p ∩ I_g| / |I_p ∪ I_g|
```

Observed interface accuracy compares the agent's `agent_interface` selection
with the candidate pose. Candidate native recovery compares the candidate pose
interface with the private native interface; these are separate metrics.

Physical plausibility is compared with `pb_valid`; native likeness is compared
with ligand heavy-atom RMSD `<= 2 Å`. Full docking success is:

```text
DockingSuccess = (ligand_RMSD <= 2 Å) AND PBValid
```

`uncertain` is not silently converted to an incorrect answer. We report:

```text
Coverage = committed_predictions / all_episodes
SelectiveAccuracy = correct_committed / committed_predictions
```

Confidence means confidence in the chosen native-likeness answer. Calibration
reports Brier score and expected calibration error over committed predictions;
uncertain predictions are excluded from the primary calibration set and their
rate is reported separately.

Centroid distance is the Euclidean distance between heavy-atom centroids. RMSD
is Kabsch-aligned and supports equivalent atom mappings where supplied.

```text
P0: RMSD <= 2 Å and PB-valid
P1: RMSD <= 2 Å and PB-invalid
P2: RMSD > 2 Å, centroid <= 2.5 Å, native-interface F1 >= 0.5
P3: 2.5 Å < centroid <= 6 Å with meaningful protein contact
P4: centroid > 6 Å, no meaningful contact, or unacceptable clash
```

Known-pocket boxes use `center = (min + max) / 2` and
`size = clip(max - min + 12 Å, 18 Å, 30 Å)` per axis. Blind-pocket episodes
are reported separately and are not mixed into the primary score. PoseBusters
and ProLIF are optional integrations and only run when installed.
