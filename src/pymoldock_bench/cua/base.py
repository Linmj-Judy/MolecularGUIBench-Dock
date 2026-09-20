from __future__ import annotations

from typing import Protocol

from ..schemas import Episode, Submission


class CUAClient(Protocol):
    """Small contract shared by Ark and deterministic offline clients."""

    def run_episode(self, episode: Episode, submission: Submission) -> Submission: ...

    def collect_artifacts(self, output_dir: str): ...
