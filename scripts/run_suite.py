#!/usr/bin/env python3
"""Run a JSONL episode manifest with the offline mock or official Ark adapter."""
import argparse, json
from pathlib import Path
import _bootstrap  # noqa: F401
from pymoldock_bench.schemas import Episode, Submission
from pymoldock_bench.cua.mock_client import MockCUAClient
from pymoldock_bench.runner.episode_runner import run_task

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--backend", choices=("mock","ark"), default="mock"); ap.add_argument("--manifest", required=True); ap.add_argument("--output", default="results/raw")
    ap.add_argument("--desktop-id"); a=ap.parse_args(); out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    if a.backend == "ark":
        from pymoldock_bench.cua.ark_client import ArkCUAClient
        skill=Path(__file__).resolve().parents[1]/".agents/skills/byted-util-ark-cua"; client=ArkCUAClient(skill); client.auth_status()
    rows=[]
    for line in Path(a.manifest).read_text().splitlines():
        if not line.strip(): continue
        item=json.loads(line); episode=Episode.model_validate(item if "episode_id" in item else json.loads(Path(item["episode"]).read_text()))
        submission=Submission(episode_id=episode.episode_id, status="completed")
        if a.backend == "mock":
            result=MockCUAClient().run_episode(episode, submission); row=result.model_dump()
        else:
            if not a.desktop_id: raise SystemExit("--desktop-id is required for --backend ark")
            row=run_task(client, a.desktop_id, episode.objective, timeout_seconds=episode.max_walltime_sec)
        path=out/f"{episode.episode_id}.json"; path.write_text(json.dumps(row, indent=2)); rows.append(row)
    print(json.dumps({"episodes":len(rows),"output":str(out)}, indent=2))
if __name__ == "__main__": main()
