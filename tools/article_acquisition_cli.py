"""File-oriented v2 acquisition and original-source inference entry points."""
from __future__ import annotations

import json
from pathlib import Path

from nabt.cli import Parser, read_certificate
from nabt.errors import NabtError
from tools import acquired_inference_v2 as pipeline
from tools import aligned_acquisition_v2 as acquisition


def _source(path):
    with path.open("rb") as stream:
        return stream.read(acquisition.MAX_SOURCE_BYTES + 1)


def main(argv=None):
    try:
        parser = Parser(prog="python -m tools.article_acquisition_cli")
        commands = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
        for name in ("read", "verify", "infer", "verify-infer"):
            command = commands.add_parser(name)
            if name in ("verify", "verify-infer"):
                command.add_argument("receipt", type=Path)
            command.add_argument("source", type=Path)
            if name in ("infer", "verify-infer"):
                command.add_argument("query", type=Path)
                command.add_argument("--time", default="unspecified")
                command.add_argument("--source-ending", choices=("wasl", "waqf"), default="wasl")
                command.add_argument("--query-ending", choices=("wasl", "waqf"), default="wasl")
            else:
                command.add_argument("--ending", choices=("wasl", "waqf"), default="wasl")
            command.add_argument("--source-id", default="input")
            command.add_argument("--revision", default="1")
            command.add_argument("--scope", default="default")
            command.add_argument("--onset", choices=("word_initial", "connected"), default="word_initial")
        args = parser.parse_args(argv)
        source = _source(args.source)
        binding = {key: getattr(args, key) for key in ("source_id", "revision", "scope", "onset")}
        if args.command in ("read", "verify"):
            binding["ending"] = args.ending
            if args.command == "read":
                report = acquisition.read_acquired(source, **binding)
                passed = report["verified"] and report["status"] == "ACQUIRED"
            else:
                report = acquisition.verify_acquired(
                    read_certificate(args.receipt, acquisition.MAX_REPORT_BYTES), text=source, **binding)
                passed = report["valid"]
        else:
            query = _source(args.query)
            binding.update({key: getattr(args, key) for key in ("time", "source_ending", "query_ending")})
            if args.command == "infer":
                report = pipeline.evaluate(source, query, **binding)
                passed = report["chain_complete"]
            else:
                report = pipeline.verify(read_certificate(args.receipt, pipeline.MAX_REPORT_BYTES),
                                         source=source, query=query, **binding)
                passed = report["valid"]
        code = 0 if passed else 2 if report["status"] in {
            "INVALID_INPUT", "INVALID_RECEIPT", "VERIFICATION_FAILED"} else 3
    except NabtError as error:
        report = acquisition._failure("RESOURCE_EXHAUSTED" if error.code == "RESOURCE_LIMIT" else
                                      "INVALID_INPUT", error.code)
        code = 3 if report["status"] == "RESOURCE_EXHAUSTED" else 2
    except OSError:
        report, code = acquisition._failure("DEFER", "IO_ERROR"), 3
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
