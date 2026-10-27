"""Separate acquisition CLI; the historically frozen ``nabt`` CLI stays exact."""
from __future__ import annotations

import json
from pathlib import Path
import sys

from .aligned_acquisition import MAX_SOURCE_BYTES, MAX_REPORT_BYTES, read_acquired, verify_acquired
from nabt.cli import Parser, read_certificate
from nabt.errors import NabtError


def main(argv=None) -> int:
    try:
        parser = Parser(prog="python -m tools.acquisition_cli")
        sub = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
        for name in ("read-acquired", "verify-acquired"):
            command = sub.add_parser(name)
            command.add_argument("document", type=Path)
            command.add_argument("--source-id", default="input")
            command.add_argument("--revision", default="1")
            command.add_argument("--scope", default="default")
            command.add_argument("--ending", choices=("wasl", "waqf"), default="wasl")
            if name == "verify-acquired":
                command.add_argument("--source", type=Path, required=True)
        args = parser.parse_args(argv)
        path = args.document if args.command == "read-acquired" else args.source
        with path.open("rb") as handle:
            raw = handle.read(MAX_SOURCE_BYTES + 1)
        binding = {"source_id": args.source_id, "revision": args.revision,
                   "scope": args.scope, "ending": args.ending}
        if args.command == "verify-acquired":
            report = verify_acquired(read_certificate(args.document, MAX_REPORT_BYTES), text=raw, **binding)
            code = 0 if report["valid"] else 3 if report["status"] in {
                "RESOURCE_EXHAUSTED", "VERIFICATION_UNAVAILABLE", "SOURCE_EVIDENCE_UNAVAILABLE"} else 2
        else:
            report = read_acquired(raw, **binding)
            code = 0 if report["status"] == "ACQUIRED" and report["verified"] else 2 if report["status"] in {
                "INVALID_INPUT", "VERIFICATION_FAILED"} else 3
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return code
    except NabtError as error:
        print(json.dumps(error.as_dict(), ensure_ascii=False), file=sys.stderr)
        return 3 if error.status == "DEFER" else 2
    except OSError as error:
        print(json.dumps({"status": "DEFER", "error": "IO_ERROR", "message": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
