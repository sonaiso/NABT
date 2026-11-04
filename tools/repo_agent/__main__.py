"""Run bounded, source-pinned repository tasks through existing NABT gates."""
import argparse
import json
from pathlib import Path
import sys
import uuid

from . import manager, policy


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inspect", help="resolve current owners, contracts and open obligations")
    for name in ("plan", "run", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--task", type=Path, required=True)
        command.add_argument("--proposal", type=Path, required=True)
        if name != "plan":
            command.add_argument("--output-dir", type=Path)
        if name == "verify":
            command.add_argument("--run-dir", type=Path, required=True)
    command = commands.add_parser("status", help="read saved state; does not revalidate it")
    command.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            result = manager.inspect()
        elif args.command == "status":
            result = {"verification": "NOT_PERFORMED", "record": policy.load(args.run_dir / "state.json")}
        else:
            task, proposal = policy.load(args.task), policy.load(args.proposal)
            if args.command == "plan":
                result = manager.plan(task, proposal)
            else:
                directory = args.output_dir or manager.ROOT / "artifacts/local/repo-agent" / uuid.uuid4().hex
                if args.command == "run":
                    result = manager.run(task, proposal, output_dir=directory)
                else:
                    result = manager.verify(args.run_dir, task, proposal, output_dir=directory)
                result = {**result, "run_dir": str(directory.absolute())}
        code = 0 if args.command in ("inspect", "status", "plan") or result.get("status") in ("READY_FOR_REVIEW", "FRESH_CHECKS_PASSED") else 1
    except (policy.AgentError, OSError, ValueError, KeyError, TypeError) as error:
        result = {"status": getattr(error, "code", "INVALID_INPUT"), "message": str(error), "publication_authority": "NONE"}
        code = 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
