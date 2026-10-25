"""Optional provenance DB CLI; no credentials are accepted on command lines."""
import argparse
import json
import os
from pathlib import Path

from .client import ROOT, initialize, load_inventory, search


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "load", "search"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--inventory")
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
            result = {"status": "SCHEMA_CREATED", "authority": "PROVENANCE_ONLY"}
        elif args.command == "load":
            result = load_inventory(connection, root=args.root)
        else:
            if not args.inventory:
                parser.error("search requires --inventory")
            result = search(connection, args.inventory, args.query, k=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
