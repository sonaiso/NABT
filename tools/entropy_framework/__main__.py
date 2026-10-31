"""python -m tools.entropy_framework {validate,report,measure,reuse}."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .measurement import measure_candidates
from .registry import (DEFAULT_REGISTRY, FrameworkError, FrameworkResourceError, load_json,
                       report_registry, validate_registry)


def _failure(status, error, code):
    # Diagnostics must remain scalar UTF-8 even when the rejected input is not.
    reason = str(error).encode("utf-8", "backslashreplace").decode("utf-8")
    print(json.dumps({"status": status, "reason": reason,
                      "semantic_authority": "NONE"}, ensure_ascii=False))
    return code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "report"):
        command = commands.add_parser(name)
        command.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    command = commands.add_parser("measure")
    command.add_argument("input", help="explicit finite candidate-ledger JSON")
    command = commands.add_parser("reuse", help="resolve existing formal contracts and executable paths")
    selection = command.add_mutually_exclusive_group()
    selection.add_argument("--family", help="existing reuse-family identity")
    selection.add_argument("--module", help="exact existing Nabt.Module identity")
    command.add_argument("--summary", action="store_true", help="compact agent startup view")
    command.add_argument("--output", type=Path, help="save the full resolved use map")
    command.add_argument("--run", metavar="ENTRYPOINT", help="delegate to an allowlisted existing CLI")
    command.add_argument("arguments", nargs=argparse.REMAINDER,
                         help="arguments after -- pass unchanged to the selected existing CLI")
    args = parser.parse_args(argv)
    try:
        if args.command == "reuse":
            from .reuse import build_reuse_report, summary
            result = build_reuse_report(family=args.family, module=args.module)
            if args.run:
                if args.family or args.module or args.output or args.summary:
                    raise FrameworkError("reuse --run is separate from report selection/output")
                from .reuse_run import run_entry
                arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
                return run_entry(args.run, arguments)
            if args.arguments:
                raise FrameworkError("reuse arguments require --run")
            if args.output:
                # Evidence is append-only by default. Reusing an old report's
                # name must not silently replace its historical observation.
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with args.output.open("x", encoding="utf-8") as handle:
                    handle.write(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
            if args.summary or args.output or (args.family is None and args.module is None):
                result = summary(result)
        elif args.command == "measure":
            result = measure_candidates(load_json(args.input))
        else:
            registry = load_json(args.registry)
            result = (validate_registry if args.command == "validate" else report_registry)(registry)
    except FrameworkResourceError as error:
        return _failure("RESOURCE_EXHAUSTED", error, 3)
    except (FrameworkError, OSError) as error:
        return _failure("INVALID_INPUT", error, 2)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
