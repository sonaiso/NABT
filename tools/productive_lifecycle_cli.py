"""Read or replay the installed clause source lifecycle with explicit events."""
import argparse
import json
from pathlib import Path

from tools import evidence_lifecycle_v1 as lifecycle
from tools import productive_lifecycle_v1 as productive
from tools.evidence_lifecycle_cli import read_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("targets")
    for name in ("read", "verify"):
        command = commands.add_parser(name)
        command.add_argument("document", type=Path)
        command.add_argument("--events", required=True, type=Path)
        command.add_argument("--source-id", default="input")
        command.add_argument("--revision", default="1")
        command.add_argument("--scope", default="default")
        command.add_argument("--ending", choices=("wasl", "waqf"), default="wasl")
        command.add_argument("--onset", choices=("word_initial", "connected"), default="word_initial")
        if name == "verify":
            command.add_argument("--source", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "targets":
            report, success = productive.installed_targets(), True
        else:
            events = read_json(args.events)
            path = args.document if args.command == "read" else args.source
            with path.open("rb") as stream:
                text = stream.read(productive.clause.MAX_SOURCE_BYTES + 1)
            binding = {key: getattr(args, key) for key in ("source_id", "revision", "scope", "ending", "onset")}
            if args.command == "read":
                report = productive.evaluate_clause(text, events=events, **binding)
                success = report["chain_complete"]
            else:
                report = productive.verify_clause(read_json(args.document, lifecycle.MAX_REPORT_BYTES, report=True),
                                                   text=text, events=events, **binding)
                success = report["valid"]
    except lifecycle.ResourceLimit as error:
        report, success = {"status": "RESOURCE_LIMIT", "reason": str(error)}, False
    except (lifecycle.InputError, ValueError) as error:
        report, success = {"status": "INVALID_INPUT", "reason": str(error)}, False
    except OSError as error:
        report, success = {"status": "UNMEASURED", "reason": str(error)}, False
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if success else 2 if report["status"] in ("INVALID_INPUT", "INVALID_RECEIPT", "VERIFICATION_FAILED", "REJECTED_IN_SCOPE") else 3


if __name__ == "__main__":
    raise SystemExit(main())
