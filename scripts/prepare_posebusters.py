#!/usr/bin/env python3
import argparse
import _bootstrap  # noqa: F401
from pymoldock_bench.data.prepare_posebusters import verify_md5, safe_extract, build_index

def main():
    p=argparse.ArgumentParser(); p.add_argument("archive"); p.add_argument("output"); p.add_argument("--index", default="data/raw/posebusters/index.json"); p.add_argument("--skip-md5", action="store_true"); a=p.parse_args()
    if not a.skip_md5 and not verify_md5(a.archive): raise SystemExit("MD5 mismatch")
    print(f"extracted={len(safe_extract(a.archive,a.output))}"); print(build_index(a.output,a.index))
if __name__ == "__main__": main()
