"""Reproducible raw-data downloader with checksum support.

URLs are supplied by the caller because upstream releases can change. No data is
silently treated as ground truth and downloads are never written to private paths.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

def download(url: str, destination: str | Path, sha256: str | None = None, md5: str | None = None, *, resume: bool = True) -> Path:
    dst = Path(destination)
    if "private" in dst.resolve().parts: raise ValueError("raw downloader cannot write private data")
    dst.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(); md5_digest = hashlib.md5()
    existing = dst.stat().st_size if resume and dst.exists() else 0
    request = Request(url, headers={"Range": f"bytes={existing}-"} if existing else {})
    with urlopen(request, timeout=60) as response:
        # Servers may ignore Range; never append a full response to a partial file.
        append = existing and getattr(response, "status", 200) == 206
        if append is False: existing = 0
        mode = "ab" if append else "wb"
        with dst.open(mode) as out:
            while chunk := response.read(1024 * 1024):
                out.write(chunk); digest.update(chunk); md5_digest.update(chunk)
    # Include existing bytes in the digest when appending.
    if append:
        digest = hashlib.sha256(dst.read_bytes()); md5_digest = hashlib.md5(dst.read_bytes())
    bad_sha = sha256 and digest.hexdigest().lower() != sha256.lower()
    bad_md5 = md5 and md5_digest.hexdigest().lower() != md5.lower()
    if bad_sha or bad_md5:
        dst.unlink(missing_ok=True)
        raise ValueError("checksum mismatch")
    return dst
