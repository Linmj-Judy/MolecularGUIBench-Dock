#!/usr/bin/env python3
"""Run one episode offline or through the official CUA adapter."""
import argparse
import _bootstrap  # noqa: F401
from pathlib import Path
from pymoldock_bench.schemas import Episode, Submission
from pymoldock_bench.cua import MockCUAClient

def main():
    p=argparse.ArgumentParser(); p.add_argument("episode"); p.add_argument("--submission"); p.add_argument("--output",default="results/raw/submission.json"); a=p.parse_args()
    episode=Episode.model_validate_json(Path(a.episode).read_text())
    if a.submission: submission=Submission.model_validate_json(Path(a.submission).read_text())
    else: submission=Submission(episode_id=episode.episode_id,status="failed",failure_category="no_submission")
    result=MockCUAClient().run_episode(episode,submission)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(result.model_dump_json(indent=2)); print(a.output)
if __name__ == "__main__": main()
