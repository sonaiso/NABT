"""CLI adapter; request-bound replay includes retrieval options and explanation."""
from pathlib import Path
from tools.evidence_lifecycle_v1 import strict_loads
from .irab import DOMAINS, MAX_REQUEST, MAX_REPORT, catalog, IrabIndex, answer, analyze, verify


def arguments(parser):
    parser.add_argument("action", choices=("catalog", "search", "answer", "analyze"))
    parser.add_argument("query", nargs="?")
    parser.add_argument("--domain", choices=DOMAINS)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--output", type=Path)


def _read(path, maximum, *, report=False):
    if path is None:
        raise ValueError("Expected --request")
    with path.open("rb") as stream:
        return strict_loads(stream.read(maximum+1), maximum_bytes=maximum, report=report)


def run(args):
    if args.action != "analyze" and (args.verify or args.request):
        raise ValueError("--request and --verify apply only to analyze")
    if args.action == "analyze":
        if args.query is not None or args.domain is not None or args.limit != 5:
            raise ValueError("Put query/domain/limit inside the independently replayed request")
        request = _read(args.request, MAX_REQUEST)
        return verify(_read(args.verify, MAX_REPORT, report=True), expected_request=request) if args.verify else analyze(request)
    if args.action == "catalog":
        return catalog()
    if args.query is None:
        raise ValueError("Expected query")
    if args.action == "answer":
        return answer(args.query, domain=args.domain, limit=args.limit)
    return IrabIndex(args.domain).search(args.query, args.limit)
