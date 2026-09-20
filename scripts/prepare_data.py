#!/usr/bin/env python3
import argparse
import _bootstrap  # noqa: F401
from pymoldock_bench.data.download import download

def main():
    p = argparse.ArgumentParser(description="Download or report benchmark data")
    p.add_argument("--url"); p.add_argument("--output"); p.add_argument("--sha256"); p.add_argument("--md5")
    p.add_argument("--dataset", choices=("astex", "posebusters")); p.add_argument("--input"); p.add_argument("--report", default="data/dataset_report.json")
    a = p.parse_args()
    if a.url:
        if not a.output: p.error("--output is required with --url")
        print(download(a.url, a.output, a.sha256, a.md5)); return
    if not a.input: p.error("--input is required without --url")
    from pymoldock_bench.data.report import write_dataset_report
    print(write_dataset_report(a.input, a.report))
if __name__ == "__main__": main()
