"""Inspect the inventory, transport finite readings, or independently replay."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools import meaning_preservation_v1 as meaning


def read_json(path, *, report=False):
    maximum = meaning.MAX_REPORT_BYTES if report else meaning.MAX_REQUEST_BYTES
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    return meaning.strict_loads(raw, maximum_bytes=maximum, report=report)


def exit_code(report):
    status = report.get("status")
    if status in ("FINITE_CONTRACT_VERIFIED", "VERIFIED_RECEIPT", "RESEARCH_METADATA_VERIFIED"):
        return 0
    if status in ("INVALID_INPUT", "INVALID_RECEIPT"):
        return 2
    if status in ("CONTRACT_VIOLATION", "DEFER", "REJECTED_IN_SCOPE"):
        return 3
    if status == "RESOURCE_EXHAUSTED":
        return 5
    return 4


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inventory")
    for name in ("authored", "productive", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--request", required=True, type=Path)
        if name == "verify":
            command.add_argument("--receipt", required=True, type=Path)
            command.add_argument("--mode", required=True, choices=("authored", "productive"))
    args = parser.parse_args(argv)
    try:
        if args.command == "inventory":
            from tools.meaning_preservation_inventory import research_inventory
            report = research_inventory()
        else:
            request = read_json(args.request)
            if args.command == "authored":
                report = meaning.evaluate_authored(request)
            elif args.command == "productive":
                report = meaning.evaluate_productive_request(request)
            else:
                report = meaning.verify(read_json(args.receipt, report=True),
                                        expected_request=request, mode=args.mode)
    except meaning.ResourceLimit:
        report = {"status": "RESOURCE_EXHAUSTED", "reason": "CLI_INPUT_RESOURCE_LIMIT", **meaning.FLAGS}
    except (meaning.InputError, ValueError, TypeError, UnicodeError):
        report = {"status": "INVALID_INPUT", "reason": "CLI_INVALID_INPUT", **meaning.FLAGS}
    except OSError:
        report = {"status": "INPUT_UNAVAILABLE", "reason": "CLI_INPUT_UNAVAILABLE", **meaning.FLAGS}
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
