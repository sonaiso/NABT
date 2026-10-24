"""Acquire immutable public-source bytes; no NABT runtime imports or writes."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha1, sha256
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
COMMIT = "4b1d2886508b435eb0377ccab96e1da96cc8ee0a"
TREE = "b4bf1236d74263961b49611e8e81e3c12667b0f8"
AUTHOR = "data/0666IbnAbiBakrZaynDinRazi"
BOOK = AUTHOR + "/0666IbnAbiBakrZaynDinRazi.MukhtarSihah"
VERSION = "0666IbnAbiBakrZaynDinRazi.MukhtarSihah.JK000107-ara1"
ITEMS = [
    (BOOK + "/" + VERSION, "mukhtar_sihah_openiti_jk000107.txt", "08c8b33915758e2cb4db8947e464c75bcc58f2e8"),
    (BOOK + "/" + VERSION + ".yml", "mukhtar_sihah_openiti_version.yml", "9dd1e26920bd22a88e5b2d01b60804c47a60a07e"),
    (AUTHOR + "/0666IbnAbiBakrZaynDinRazi.yml", "mukhtar_sihah_openiti_author.yml", "7ae618daf6077cbd66fd989fcc6dba7bd6a77c5e"),
    ("README.md", "openiti_0675ah_readme.txt", "855a2c59937f3b7eab47021c7bf7f628af798936"),
]


def main() -> None:
    rows = []
    for path, destination, expected_blob in ITEMS:
        url = f"https://raw.githubusercontent.com/OpenITI/0675AH/{COMMIT}/{path}"
        request = Request(url, headers={"User-Agent": "NABT-source-evidence-audit/1.0"})
        with urlopen(request, timeout=45) as response:
            raw = response.read()
            final_url = response.geturl()
        blob = sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        if blob != expected_blob:
            raise ValueError(f"Git blob mismatch for {path}")
        raw.decode("utf-8")
        with (HERE / destination).open("xb") as stream:
            stream.write(raw)
        rows.append({
            "repository": "OpenITI/0675AH", "commit": COMMIT, "tree": TREE,
            "path": path, "url": url, "final_url": final_url,
            "local_path": destination, "bytes": len(raw),
            "sha256": sha256(raw).hexdigest(), "git_blob_sha1": blob,
            "git_blob_matches_pinned_tree": True,
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        })
    result = {
        "schema": "nabt.public-source-acquisition.v1",
        "purpose": "Independent lexical witness for vocalized hasiba; acquired after baseline review, not blind.",
        "scope": "Exact digital OpenITI bytes and upstream metadata; no printed-page or manuscript collation claimed.",
        "files": rows,
    }
    with (HERE / "mukhtar_openiti_retrieval_v1.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
