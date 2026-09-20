#!/usr/bin/env python3
import argparse
import _bootstrap  # noqa: F401
from pymoldock_bench.utils.manifest import write_run_manifest

ap=argparse.ArgumentParser(); ap.add_argument("--output",default="results/run_manifest.json"); ap.add_argument("--config"); ap.add_argument("--skill-path",default=".agents/skills/byted-util-ark-cua"); a=ap.parse_args()
print(write_run_manifest(a.output, config_path=a.config, skill_path=a.skill_path))
