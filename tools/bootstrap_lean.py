#!/usr/bin/env python3
"""Install the pinned official Linux x86_64 Lean toolchain after digest checking.

No shell installation script is downloaded or executed. Requires tar and unzstd.
The destination is local to the caller; system toolchains are left alone.
"""

import argparse
import hashlib
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import http.client
import urllib.error
import urllib.request

VERSION = "4.34.1"
ARCHIVE = f"lean-{VERSION}-linux.tar.zst"
URL = f"https://github.com/leanprover/lean4/releases/download/v{VERSION}/{ARCHIVE}"
SHA256 = "47bf4bbd78f70c2e9670598ab7124d92b6efb7330ff33e5fbb4030f6fd72e4e4"


def download_verified(archive, *, attempts=5):
    """Retry transient transport failures; never reuse partial/unverified bytes."""
    partial = archive.with_suffix(archive.suffix + ".partial")
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(URL, headers={"User-Agent": "NABT-pinned-toolchain/1"})
            with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as out:
                shutil.copyfileobj(response, out, length=1024 * 1024)
            if digest(partial) != SHA256:
                raise ValueError("Official toolchain archive failed SHA-256 verification")
            partial.replace(archive)
            return
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.IncompleteRead) as exc:
            transient = not isinstance(exc, urllib.error.HTTPError) or exc.code in {408, 429, 500, 502, 503, 504}
            if not transient or attempt + 1 == attempts:
                raise
            delay = min(2 ** attempt, 16)
            print(f"Transient toolchain download failure; retry {attempt + 2}/{attempts} in {delay}s",
                  file=sys.stderr)
            time.sleep(delay)
        finally:
            partial.unlink(missing_ok=True)


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    if platform.system() != "Linux" or platform.machine() not in {"x86_64", "AMD64"}:
        parser.error("This installer pins Linux x86_64; install lean-toolchain with elan on other platforms")
    if shutil.which("tar") is None or shutil.which("unzstd") is None:
        parser.error("Install tar and zstd before using this installer")
    root = args.destination.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    archive = root / ARCHIVE
    if not archive.is_file() or digest(archive) != SHA256:
        download_verified(archive)
    subprocess.run(["tar", "--no-same-owner", "--no-same-permissions", "--use-compress-program=unzstd",
                    "-xf", str(archive), "-C", str(root)], check=True)
    lean = root / f"lean-{VERSION}-linux" / "bin" / "lean"
    subprocess.run([str(lean), "--version"], check=True)
    print(f"Verified toolchain: {lean.parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
