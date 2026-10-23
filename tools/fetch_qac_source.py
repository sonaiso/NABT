#!/usr/bin/env python3
"""Fetch an unmodified, pinned external QAC source, retaining its notices.

This is evaluation/source acquisition, not an installed runtime dependency.
The decoded original must match the published source identity. No annotation
or Quranic text is edited or redistributed in the NABT package.
"""

import argparse
import gzip
from hashlib import sha256
import io
import json
from pathlib import Path
import urllib.request

URL = ("https://raw.githubusercontent.com/Saleh1967/Alghanem/"
       "9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/"
       "corpora/qac/quranic-corpus-morphology-0.4.txt.gz")
DECODED_SHA256 = "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46"
MAX_BYTES = 16 * 1024 * 1024


def checked(raw):
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
        decoded = stream.read(MAX_BYTES + 1)
    if len(decoded) > MAX_BYTES or sha256(decoded).hexdigest() != DECODED_SHA256:
        raise ValueError("External QAC source differs from its pinned decoded identity")
    return len(decoded)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cached = args.output.exists()
    if cached:
        raw = args.output.read_bytes()
    else:
        with urllib.request.urlopen(URL, timeout=45) as response:
            raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Source response exceeds the download budget")
    length = checked(raw)
    if not cached:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(raw)
    print(json.dumps({"source": URL, "decoded_sha256": DECODED_SHA256,
                      "decoded_bytes": length, "compressed_sha256": sha256(raw).hexdigest(),
                      "output": str(args.output), "already_present": cached,
                      "scope": "UNMODIFIED_EXTERNAL_SOURCE_NOT_A_RUNTIME_ANSWER_DICTIONARY"}))


if __name__ == "__main__":
    main()
