"""Additive authored-episode CLI; historical NABT commands are unchanged."""
import argparse
import json
from pathlib import Path

from tools import evidence_lifecycle_v1 as lifecycle


def read_json(path, maximum=lifecycle.MAX_REQUEST_BYTES, *, report=False):
    with Path(path).open("rb") as stream:
        return lifecycle.strict_loads(stream.read(maximum + 1), maximum_bytes=maximum, report=report)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("episode", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("report", type=Path)
    verify.add_argument("--episode", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        episode = read_json(args.episode)
        if args.command == "evaluate":
            report = lifecycle.evaluate_episode(episode)
            success = report["native_checked"] and report["decision_complete"]
        else:
            report = lifecycle.verify_episode(read_json(args.report, lifecycle.MAX_REPORT_BYTES), expected_episode=episode)
            success = report["valid"]
    except lifecycle.ResourceLimit as error:
        report, success = {"status": "RESOURCE_LIMIT", "reason": str(error)}, False
    except (lifecycle.InputError, ValueError) as error:
        report, success = {"status": "INVALID_INPUT", "reason": str(error)}, False
    except OSError as error:
        report, success = {"status": "UNMEASURED", "reason": str(error)}, False
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if success else 2 if report["status"] in ("INVALID_INPUT", "INVALID_RECEIPT", "VERIFICATION_FAILED") else 3


if __name__ == "__main__":
    raise SystemExit(main())
