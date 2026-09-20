# Implementation notes

Phase A is implemented as an offline-first MVP. Ground truth is kept in private
paths and submissions contain only agent-visible outputs. Real ARK CUA calls are
isolated behind `ArkCUAClient`; no credential is accepted by this repository.

The local interface audit on 2026-09-20 used the checked-in Skill at
`.agents/skills/byted-util-ark-cua` (version 1.0.7), `arkcli 1.0.33`, and the
current `cua.py task run/status/result` help output. The machine currently has
no Agent Plan Max profile, so real CUA execution remains an explicit external
integration step; all schemas, isolation checks, and evaluation run offline.
The PoseBusters archive found in `data/raw` is truncated and is rejected by the
ZIP integrity check rather than silently extracted.
