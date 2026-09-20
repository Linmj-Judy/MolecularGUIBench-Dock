#!/usr/bin/env python3
import argparse
import _bootstrap  # noqa: F401
from pathlib import Path
from pymoldock_bench.schemas import Episode, Submission, GroundTruth
from pymoldock_bench.eval import evaluate

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("episode"); ap.add_argument("submission"); ap.add_argument("ground_truth")
    a = ap.parse_args()
    result = evaluate(Episode.model_validate_json(Path(a.episode).read_text()), Submission.model_validate_json(Path(a.submission).read_text()), GroundTruth.model_validate_json(Path(a.ground_truth).read_text()))
    print(result.model_dump_json(indent=2))
if __name__ == "__main__": main()
