from __future__ import annotations
from .episode_runner import run_task

def run_suite(client, episodes, desktop: str, *, poll_seconds=5, timeout_seconds=1800):
    # Deliberately sequential: one desktop must never receive concurrent GUI tasks.
    return [run_task(client, desktop, e.objective, poll_seconds=poll_seconds, timeout_seconds=timeout_seconds) for e in episodes]
