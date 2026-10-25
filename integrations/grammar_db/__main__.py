"""Optional DB CLI. Password/DSN is read from the environment, never flags."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .client import initialize, load_catalog, search


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "load", "search"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--snapshot")
    parser.add_argument("--query", default="")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    dsn = os.environ.get("NABT_DATABASE_URL")
    if not dsn:
        parser.error("set NABT_DATABASE_URL outside the repository")
    import psycopg
    with psycopg.connect(dsn) as connection:
        if args.command == "init":
            initialize(connection)
            result = {"status": "SCHEMA_CREATED", "authority": "RETRIEVAL_ONLY"}
        elif args.command == "load":
            from tools.grammar_catalog.catalog import build_catalog
            digest = load_catalog(connection, build_catalog(root=args.root), root=args.root)
            result = {"status": "SNAPSHOT_IMPORTED", "snapshot_sha": digest, "authority": "RETRIEVAL_ONLY"}
        else:
            if not args.snapshot:
                parser.error("search requires --snapshot")
            result = search(connection, args.snapshot, args.query, k=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
