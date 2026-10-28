"""python -m tools.entropy_framework {validate,report,measure}."""
from __future__ import annotations

import argparse
import json
import sys

from .measurement import measure_candidates
from .registry import (DEFAULT_REGISTRY, FrameworkError, load_json,
                       report_registry, validate_registry)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "report"):
        command = commands.add_parser(name)
        command.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    command = commands.add_parser("measure")
    command.add_argument("input", help="explicit finite candidate-ledger JSON")
    args = parser.parse_args(argv)
    try:
        if args.command == "measure":
            result = measure_candidates(load_json(args.input))
        else:
            registry = load_json(args.registry)
            result = (validate_registry if args.command == "validate" else report_registry)(registry)
    except (FrameworkError, OSError) as error:
        print(json.dumps({"status": "INVALID_INPUT", "reason": str(error),
                          "semantic_authority": "NONE"}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
