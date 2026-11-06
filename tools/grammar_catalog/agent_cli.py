"""Shared progressive agent/proof navigation through grammar-catalog."""
from pathlib import Path
from tools.evidence_lifecycle_v1 import strict_loads


def arguments(parser):
    parser.add_argument("action", choices=("catalog", "search", "plan", "proofs", "gate", "transport"))
    parser.add_argument("value", nargs="?")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--output", type=Path)


def read(path, *, report=False):
    if path is None:
        raise ValueError("This action requires --request")
    maximum = 8 * 1048576 if report else 2 * 1048576
    with path.open("rb") as stream:
        return strict_loads(stream.read(maximum + 1), maximum_bytes=maximum, report=report)


def run(args):
    from tools.lexical_training import agent_plan as owner
    if args.verify and args.action not in ("gate", "transport"):
        raise ValueError("--verify applies to gate or transport")
    if args.action == "catalog":
        result = owner.build_report()
        return owner.summary(result) if args.summary else result
    if args.action in ("search", "plan", "proofs"):
        if args.value is None:
            raise ValueError("Expected a query or profile identity")
        if args.action == "search":
            return owner.search(args.value, limit=args.limit)
        return (owner.plan_for if args.action == "plan" else owner.proofs)(args.value)
    request = read(args.request)
    if args.action == "transport":
        from .unicode_transport import transcode, verify
        return verify(read(args.verify, report=True), expected_request=request) if args.verify else transcode(request)
    return owner.verify_gate(read(args.verify, report=True), expected_request=request) if args.verify else owner.factor_gate(request)
