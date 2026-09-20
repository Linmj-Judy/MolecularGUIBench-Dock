#!/usr/bin/env python3
import argparse, json, csv
import _bootstrap  # noqa: F401
from pathlib import Path
from pymoldock_bench.eval import evaluate
from pymoldock_bench.eval.aggregate import summarize_results
from pymoldock_bench.schemas import Episode, Submission, GroundTruth

def main():
    p=argparse.ArgumentParser(); p.add_argument("manifest",help="JSON list of {episode,submission,ground_truth} paths"); p.add_argument("--output",default="results/summary"); a=p.parse_args()
    rows=[]
    for item in json.loads(Path(a.manifest).read_text()):
        e=Episode.model_validate_json(Path(item["episode"]).read_text()); s=Submission.model_validate_json(Path(item["submission"]).read_text()); g=GroundTruth.model_validate_json(Path(item["ground_truth"]).read_text()); rows.append(evaluate(e,s,g).model_dump())
    out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    (out/"episodes.json").write_text(json.dumps(rows,indent=2))
    (out/"summary.json").write_text(json.dumps(summarize_results(rows),indent=2))
    if rows:
        with (out/"episodes.csv").open("w",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=sorted(rows[0])); writer.writeheader(); writer.writerows(rows)
    try:
        import pandas as pd
        pd.DataFrame(rows).to_parquet(out/"episodes.parquet",index=False)
    except (ImportError, Exception):
        pass
    print(out)
if __name__ == "__main__": main()
