"""Additive productive-clause entry point; the frozen nabt CLI is unchanged."""
from __future__ import annotations

import json
from pathlib import Path
import sys

from nabt.cli import Parser, read_certificate
from nabt.errors import NabtError
from tools import productive_clause_v1 as clause


def main(argv=None):
    try:
        parser = Parser(prog="python -m tools.productive_clause_cli")
        sub = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
        for name in ("read", "verify"):
            command = sub.add_parser(name)
            command.add_argument("document", type=Path)
            command.add_argument("--source-id", default="input")
            command.add_argument("--revision", default="1")
            command.add_argument("--scope", default="default")
            command.add_argument("--ending", choices=("wasl", "waqf"), default="wasl")
            command.add_argument("--onset", choices=("word_initial", "connected"), default="word_initial")
            if name == "verify":
                command.add_argument("--source", type=Path, required=True)
        args = parser.parse_args(argv)
        path = args.document if args.command == "read" else args.source
        with path.open("rb") as stream:
            text = stream.read(clause.MAX_SOURCE_BYTES + 1)
        binding = {key: getattr(args, key) for key in ("source_id", "revision", "scope", "ending", "onset")}
        if args.command == "read":
            report = clause.evaluate(text, **binding)
            success = report["chain_complete"]
        else:
            report = clause.verify(read_certificate(args.document, clause.MAX_REPORT_BYTES), text=text, **binding)
            success = report["valid"]
        code = 0 if success else 2 if report["status"] in {
            "INVALID_INPUT", "INVALID_RECEIPT", "VERIFICATION_FAILED", "REJECTED_IN_SCOPE"} else 3
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
        return code
    except NabtError as error:
        print(json.dumps(error.as_dict(), ensure_ascii=False), file=sys.stderr)
        return 3 if error.status == "DEFER" else 2
    except OSError as error:
        print(json.dumps({"status": "DEFER", "error": "IO_ERROR", "message": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
