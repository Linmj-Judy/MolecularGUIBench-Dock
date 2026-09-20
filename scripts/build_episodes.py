#!/usr/bin/env python3
import argparse
import _bootstrap  # noqa: F401
from pymoldock_bench.episodes.build_diagnosis import build_diagnosis_episode

def main():
    p=argparse.ArgumentParser(); p.add_argument("source", nargs="?"); p.add_argument("output", nargs="?"); p.add_argument("--source", dest="source_opt"); p.add_argument("--output", dest="output_opt"); p.add_argument("--episode-id",required=True); p.add_argument("--target-id",required=True); p.add_argument("--split",default="dev",choices=("dev","test")); a=p.parse_args()
    source=a.source or a.source_opt; output=a.output or a.output_opt
    if not source or not output: p.error("source and output are required")
    print(build_diagnosis_episode(source,output,episode_id=a.episode_id,target_id=a.target_id,split=a.split))
if __name__ == "__main__": main()
