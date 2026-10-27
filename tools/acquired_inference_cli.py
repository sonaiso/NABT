"""Run the source-bound acquisition / existing PR 34 inference composition."""
from __future__ import annotations

import json
from pathlib import Path

from nabt.cli import Parser, read_certificate
from nabt.errors import NabtError
from tools import acquired_inference as pipeline
from tools.aligned_acquisition import MAX_SOURCE_BYTES


def main(argv=None):
    try:
        parser = Parser(prog="python -m tools.acquired_inference_cli")
        commands = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
        for name in ("infer", "verify"):
            command = commands.add_parser(name)
            if name == "verify":
                command.add_argument("receipt", type=Path)
            command.add_argument("source", type=Path)
            command.add_argument("query", type=Path)
            command.add_argument("--source-id", default="input")
            command.add_argument("--revision", default="1")
            command.add_argument("--scope", default="default")
            command.add_argument("--time", default="unspecified")
            command.add_argument("--source-ending", choices=("wasl", "waqf"), default="wasl")
            command.add_argument("--query-ending", choices=("wasl", "waqf"), default="wasl")
        args = parser.parse_args(argv)
        with args.source.open("rb") as stream:
            source = stream.read(MAX_SOURCE_BYTES + 1)
        with args.query.open("rb") as stream:
            query = stream.read(MAX_SOURCE_BYTES + 1)
        binding = {key: getattr(args, key) for key in
                   ("source_id", "revision", "scope", "time", "source_ending", "query_ending")}
        if args.command == "verify":
            report = pipeline.verify(read_certificate(args.receipt, pipeline.MAX_REPORT_BYTES),
                                     source=source, query=query, **binding)
            passed = report["valid"]
        else:
            report = pipeline.evaluate(source, query, **binding)
            passed = report["chain_complete"]
        code = 0 if passed else 2 if report["status"] in {"INVALID_INPUT", "INVALID_RECEIPT"} else 3
    except NabtError as error:
        report, code = error.as_dict(), 2
    except OSError:
        report, code = {"status": "IO_ERROR", "verified": False}, 3
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
